"""Task Core — Resource locks with TTL (S1-T6)."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import Lock


def _utcnow() -> datetime:
    return datetime.utcnow()


class LockConflictError(ValueError):
    """Raised when a resource is already locked by another owner."""
    def __init__(self, resource: str, owner: str):
        super().__init__(f"Resource '{resource}' is locked by '{owner}'")


class LockManager:
    """Resource locks with owner and TTL.

    Expired locks are silently reclaimed on next acquire attempt.
    Uses naive UTC datetimes for SQLite compatibility.
    """

    DEFAULT_TTL = timedelta(seconds=300)

    def __init__(self, session: Session):
        self.session = session

    def acquire(self, resource: str, owner: str,
                ttl: timedelta = DEFAULT_TTL) -> Lock:
        """Acquire a lock on a resource.

        If the lock exists but is expired, it is reclaimed.
        Raises LockConflictError if locked by another owner.
        """
        now = _utcnow()
        existing = self.session.scalar(
            select(Lock).where(Lock.resource == resource)
        )

        if existing is not None:
            expires_at = existing.acquired_at + timedelta(seconds=existing.ttl_seconds)
            if now < expires_at and existing.owner != owner:
                raise LockConflictError(resource, existing.owner)
            # Expired or same owner — reclaim
            if existing.owner == owner:
                # Extend
                existing.ttl_seconds = int(ttl.total_seconds())
                existing.acquired_at = now
                self.session.flush()
                return existing
            else:
                # Expired — delete and create new
                self.session.delete(existing)
                self.session.flush()

        lock = Lock(
            resource=resource,
            owner=owner,
            ttl_seconds=int(ttl.total_seconds()),
            acquired_at=now,
        )
        self.session.add(lock)
        self.session.flush()
        return lock

    def release(self, resource: str, owner: str) -> bool:
        """Release a lock. Returns True if lock was held and released."""
        existing = self.session.scalar(
            select(Lock).where(Lock.resource == resource)
        )
        if existing is None:
            return False
        if existing.owner != owner:
            return False
        self.session.delete(existing)
        self.session.flush()
        return True

    def is_locked(self, resource: str) -> bool:
        """Check if resource is currently locked (non-expired)."""
        now = _utcnow()
        existing = self.session.scalar(
            select(Lock).where(Lock.resource == resource)
        )
        if existing is None:
            return False
        expires_at = existing.acquired_at + timedelta(seconds=existing.ttl_seconds)
        return now < expires_at

    def expire_stale(self) -> int:
        """Remove all locks whose TTL has expired. Returns count removed."""
        now = _utcnow()
        locks = self.session.scalars(select(Lock)).all()
        count = 0
        for lock in locks:
            expires_at = lock.acquired_at + timedelta(seconds=lock.ttl_seconds)
            if now >= expires_at:
                self.session.delete(lock)
                count += 1
        if count:
            self.session.flush()
        return count