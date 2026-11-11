"""Task Core — Job dispatcher with lease/heartbeat/timeout (S1-T4)."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .models import Job, JobStatus
from .status import StatusMachine


class Dispatcher:
    """Acquires and manages job leases.

    Lease lifecycle:
        queued → leased (acquire) → running (heartbeat) → done/failed
        leased → expired (TTL exceeded, no heartbeat)
        leased → queued (lease expired, re-queue for retry)
        running → queued (retry on failure)
    """

    DEFAULT_LEASE_TTL = timedelta(seconds=60)
    DEFAULT_HEARTBEAT_INTERVAL = timedelta(seconds=15)
    MAX_ATTEMPTS = 3

    def __init__(self, session: Session):
        self.session = session

    def acquire(self, step_id: str, worker_id: str,
                lease_ttl: timedelta = DEFAULT_LEASE_TTL) -> Optional[Job]:
        """Acquire the next queued job for a step.

        Returns None if no queued job is available or max attempts exceeded.
        """
        job = self.session.scalar(
            select(Job)
            .where(Job.step_id == step_id, Job.status == JobStatus.QUEUED)
            .order_by(Job.attempt.asc())
            .limit(1)
        )
        if job is None:
            return None

        if job.attempt > self.MAX_ATTEMPTS:
            return None

        job.status = JobStatus.LEASED
        job.worker_id = worker_id
        job.lease_expires_at = datetime.now(timezone.utc) + lease_ttl
        job.heartbeat_at = datetime.now(timezone.utc)
        self.session.flush()
        return job

    def heartbeat(self, job: Job) -> bool:
        """Extend lease. Returns False if lease has expired."""
        now = datetime.now(timezone.utc)
        if job.lease_expires_at and now > job.lease_expires_at:
            job.status = JobStatus.EXPIRED
            self.session.flush()
            return False

        job.heartbeat_at = now
        job.lease_expires_at = now + self.DEFAULT_LEASE_TTL
        self.session.flush()
        return True

    def start(self, job: Job) -> None:
        """Transition leased → running."""
        StatusMachine.validate("job", job.status.value, JobStatus.RUNNING.value)
        job.status = JobStatus.RUNNING
        job.heartbeat_at = datetime.now(timezone.utc)
        self.session.flush()

    def complete(self, job: Job, result: Optional[dict] = None) -> None:
        """Mark job as done."""
        StatusMachine.validate("job", job.status.value, JobStatus.DONE.value)
        job.status = JobStatus.DONE
        job.result_json = (
            __import__("json").dumps(result) if result else None
        )
        job.lease_expires_at = None
        self.session.flush()

    def fail(self, job: Job, error: Optional[dict] = None) -> None:
        """Mark job as failed; may be retried."""
        StatusMachine.validate("job", job.status.value, JobStatus.FAILED.value)
        job.status = JobStatus.FAILED
        job.error_json = (
            __import__("json").dumps(error) if error else None
        )
        self.session.flush()

    def retry(self, job: Job) -> Optional[Job]:
        """Re-queue a failed job. Returns None if max attempts exceeded."""
        if job.attempt >= self.MAX_ATTEMPTS:
            job.status = JobStatus.EXPIRED
            self.session.flush()
            return None

        StatusMachine.validate("job", job.status.value, JobStatus.QUEUED.value)
        job.status = JobStatus.QUEUED
        job.attempt += 1
        job.worker_id = None
        job.lease_expires_at = None
        job.heartbeat_at = None
        self.session.flush()
        return job

    def recover_expired(self, step_id: Optional[str] = None) -> int:
        """Find jobs with expired leases and either re-queue or expire them.

        Returns count of recovered jobs.
        """
        now = datetime.now(timezone.utc)
        q = (
            select(Job)
            .where(
                Job.lease_expires_at.isnot(None),
                Job.lease_expires_at < now,
                Job.status.in_([JobStatus.LEASED, JobStatus.RUNNING]),
            )
        )
        if step_id:
            q = q.where(Job.step_id == step_id)

        expired_jobs = self.session.scalars(q).all()

        count = 0
        for job in expired_jobs:
            if job.attempt < self.MAX_ATTEMPTS:
                job.status = JobStatus.QUEUED
                job.attempt += 1
            else:
                job.status = JobStatus.EXPIRED
            job.worker_id = None
            job.lease_expires_at = None
            job.heartbeat_at = None
            count += 1

        self.session.flush()
        return count