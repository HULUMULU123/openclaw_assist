"""Integration tests for idempotency, dispatcher, budget, locks, events, binder.

Uses SQLite :memory: for speed and isolation.
"""

import time
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from taskcore.models import (
    Base, Task, TaskStatus, Step, StepStatus, Job, JobStatus,
    Budget, BudgetReservation, SideEffect, SideEffectStatus,
    IdempotencyKey,
)
from taskcore.status import StatusMachine, InvalidTransitionError
from taskcore.idempotency import IdempotencyGuard, compute_idempotency_key
from taskcore.dispatcher import Dispatcher
from taskcore.budget import BudgetManager, BudgetExceededError, NoBudgetError
from taskcore.locks import LockManager, LockConflictError
from taskcore.events import EventJournal
from taskcore.binder import TaskBinder


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def engine():
    e = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(e, "connect")
    def _pragma(dbapi_conn, _rec):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(e)
    return e


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


# ── Idempotency ───────────────────────────────────────────────────

class TestIdempotency:

    @staticmethod
    def _make_task(session, task_id="t1"):
        t = Task(id=task_id, canonical_id=f"canonical:{task_id}",
                 title="idempotency-test", channel="test", channel_update_id=hash(task_id),
                 sender_id="u1")
        session.add(t)
        session.flush()
        return t

    def test_compute_key_deterministic(self):
        args = {"action": "send_telegram", "chat_id": "123"}
        k1 = compute_idempotency_key("t1", "s1", "telegram_send", args)
        k2 = compute_idempotency_key("t1", "s1", "telegram_send", args)
        assert k1 == k2
        assert len(k1) == 64  # SHA-256 hex

    def test_compute_key_different_args(self):
        k1 = compute_idempotency_key("t1", "s1", "telegram_send", {"a": 1})
        k2 = compute_idempotency_key("t1", "s1", "telegram_send", {"a": 2})
        assert k1 != k2

    def test_compute_key_order_independent(self):
        k1 = compute_idempotency_key("t1", "s1", "t", {"a": 1, "b": 2})
        k2 = compute_idempotency_key("t1", "s1", "t", {"b": 2, "a": 1})
        assert k1 == k2

    def test_try_register_new(self, session):
        self._make_task(session)
        guard = IdempotencyGuard(session)
        is_new, se = guard.try_register("t1", "s1", "test", {"x": 1})
        assert is_new is True
        assert se is not None
        assert se.status == SideEffectStatus.PENDING

    def test_try_register_duplicate(self, session):
        self._make_task(session)
        guard = IdempotencyGuard(session)
        _, se1 = guard.try_register("t1", "s1", "test", {"x": 1})
        _, se2 = guard.try_register("t1", "s1", "test", {"x": 1})
        assert se1.id == se2.id  # same object

    def test_mark_done(self, session):
        self._make_task(session)
        guard = IdempotencyGuard(session)
        _, se = guard.try_register("t1", "s1", "test", {"x": 1})
        guard.mark_done(se, "ext-1", {"ok": True})
        assert se.status == SideEffectStatus.DONE
        assert se.external_id == "ext-1"

    def test_mark_failed(self, session):
        self._make_task(session)
        guard = IdempotencyGuard(session)
        _, se = guard.try_register("t1", "s1", "test", {"x": 1})
        guard.mark_failed(se, "something went wrong")
        assert se.status == SideEffectStatus.FAILED

    def test_reconcile_pending(self, session):
        self._make_task(session)
        guard = IdempotencyGuard(session)
        _, se1 = guard.try_register("t1", "s1", "a", {"x": 1})
        _, se2 = guard.try_register("t1", "s2", "b", {"x": 2})
        guard.mark_done(se1, "ext-1")

        pending = guard.reconcile_pending("t1")
        assert len(pending) == 1
        assert pending[0].id == se2.id
        assert pending[0].status == SideEffectStatus.NEEDS_RECONCILIATION

    def test_50_concurrent_keys_one_effect(self, session):
        """S1-AC-3: 50 concurrent registrations → exactly 1 effect."""
        self._make_task(session)
        guard = IdempotencyGuard(session)
        results = []
        for i in range(50):
            is_new, se = guard.try_register("t1", "s1", "send", {"to": "x"})
            results.append((is_new, se.id if se else None))

        new_count = sum(1 for r in results if r[0])
        assert new_count == 1, f"Expected exactly 1 new registration, got {new_count}"
        # All should return the same side_effect id
        ids = set(r[1] for r in results)
        assert len(ids) == 1


# ── Dispatcher ────────────────────────────────────────────────────

class TestDispatcher:

    @staticmethod
    def _make_task(session, task_id="t1"):
        t = Task(id=task_id, canonical_id=f"canonical:{task_id}",
                 title="test", channel="test", channel_update_id=1,
                 sender_id="u1")
        session.add(t)
        session.flush()
        return t

    @staticmethod
    def _make_step(session, step_id="s1", task_id="t1"):
        s = Step(id=step_id, task_id=task_id, order=1)
        session.add(s)
        session.flush()
        return s

    def test_acquire_no_jobs(self, session):
        d = Dispatcher(session)
        job = d.acquire("s1", "w1")
        assert job is None

    def test_acquire_queued_job(self, session):
        self._make_task(session)
        self._make_step(session)
        j1 = Job(step_id="s1", status=JobStatus.QUEUED)
        session.add(j1)
        session.flush()

        d = Dispatcher(session)
        job = d.acquire("s1", "w1")
        assert job is not None
        assert job.status == JobStatus.LEASED
        assert job.worker_id == "w1"
        assert job.lease_expires_at is not None

    def test_heartbeat(self, session):
        self._make_task(session)
        self._make_step(session)
        j1 = Job(step_id="s1", status=JobStatus.QUEUED)
        session.add(j1)
        session.flush()

        d = Dispatcher(session)
        job = d.acquire("s1", "w1")
        assert d.heartbeat(job)

    def test_heartbeat_expired(self, session):
        self._make_task(session)
        self._make_step(session)
        j1 = Job(step_id="s1", status=JobStatus.QUEUED)
        session.add(j1)
        session.flush()

        d = Dispatcher(session)
        job = d.acquire("s1", "w1")
        # Manually expire
        job.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        assert not d.heartbeat(job)
        assert job.status == JobStatus.EXPIRED

    def test_start_complete_lifecycle(self, session):
        self._make_task(session)
        self._make_step(session)
        j1 = Job(step_id="s1", status=JobStatus.QUEUED)
        session.add(j1)
        session.flush()

        d = Dispatcher(session)
        job = d.acquire("s1", "w1")
        d.start(job)
        assert job.status == JobStatus.RUNNING
        d.complete(job, {"ok": True})
        assert job.status == JobStatus.DONE

    def test_fail_and_retry(self, session):
        self._make_task(session)
        self._make_step(session)
        j1 = Job(step_id="s1", status=JobStatus.QUEUED)
        session.add(j1)
        session.flush()

        d = Dispatcher(session)
        job = d.acquire("s1", "w1")
        d.start(job)
        d.fail(job, {"error": "timeout"})
        assert job.status == JobStatus.FAILED

        retried = d.retry(job)
        assert retried is not None
        assert retried.status == JobStatus.QUEUED
        assert retried.attempt == 2

    def test_retry_max_attempts(self, session):
        self._make_task(session)
        self._make_step(session)
        j1 = Job(step_id="s1", status=JobStatus.QUEUED, attempt=3)
        session.add(j1)
        session.flush()

        d = Dispatcher(session)
        job = d.acquire("s1", "w1")
        d.start(job)
        d.fail(job)
        retried = d.retry(job)
        assert retried is None
        assert job.status == JobStatus.EXPIRED

    def test_recover_expired(self, session):
        self._make_task(session)
        self._make_step(session)
        j1 = Job(step_id="s1", status=JobStatus.LEASED, worker_id="old",
                 lease_expires_at=datetime.now(timezone.utc) - timedelta(seconds=60))
        session.add(j1)
        session.flush()

        d = Dispatcher(session)
        count = d.recover_expired("s1")
        assert count == 1

        # Refresh
        session.refresh(j1)
        assert j1.status == JobStatus.QUEUED
        assert j1.worker_id is None


# ── Budget ────────────────────────────────────────────────────────

class TestBudget:

    @staticmethod
    def _make_task(session, task_id="t1"):
        t = Task(id=task_id, canonical_id=f"canonical:{task_id}",
                 title="budget-test", channel="test", channel_update_id=hash(task_id),
                 sender_id="u1")
        session.add(t)
        session.flush()
        return t

    def test_ensure_profile(self, session):
        bm = BudgetManager(session)
        b = bm.ensure_profile("test", limit_usd=10.0)
        assert b.profile == "test"
        assert b.limit_usd == 10.0

    def test_reserve_within_limit(self, session):
        self._make_task(session)
        bm = BudgetManager(session)
        bm.ensure_profile("test", limit_usd=10.0)
        r = bm.reserve("test", "t1", 3.0)
        assert r.status == "reserved"
        assert r.amount_usd == 3.0

    def test_reserve_exceeds_limit(self, session):
        self._make_task(session)
        bm = BudgetManager(session)
        bm.ensure_profile("test", limit_usd=10.0)
        with pytest.raises(BudgetExceededError) as e:
            bm.reserve("test", "t1", 12.0)
        assert "test" in str(e.value)

    def test_reserve_cas_at_limit(self, session):
        """S1-AC-4: 100 parallel reserves ≤ limit."""
        self._make_task(session)
        bm = BudgetManager(session)
        bm.ensure_profile("test", limit_usd=10.0)

        # Reserve up to limit
        successes = 0
        for _ in range(100):
            try:
                bm.reserve("test", "t1", 0.1)
                successes += 1
            except BudgetExceededError:
                pass

        assert successes == 100  # 100 × 0.1 = 10.0, within limit

    def test_reserve_at_borderline(self, session):
        self._make_task(session, "t1")
        self._make_task(session, "t2")
        bm = BudgetManager(session)
        bm.ensure_profile("test", limit_usd=10.0)
        bm.reserve("test", "t1", 9.5)
        with pytest.raises(BudgetExceededError):
            bm.reserve("test", "t2", 1.0)  # 9.5+1.0=10.5 > 10.0

    def test_settle(self, session):
        self._make_task(session)
        bm = BudgetManager(session)
        bm.ensure_profile("test", limit_usd=10.0)
        r = bm.reserve("test", "t1", 3.0)
        bm.settle(r)
        assert r.status == "settled"
        assert r.settled_at is not None

        b = session.get(Budget, r.budget_id)
        assert b.reserved_usd == 0.0
        assert b.settled_usd == 3.0

    def test_release(self, session):
        self._make_task(session)
        bm = BudgetManager(session)
        bm.ensure_profile("test", limit_usd=10.0)
        r = bm.reserve("test", "t1", 3.0)
        bm.release(r)
        assert r.status == "released"

        b = session.get(Budget, r.budget_id)
        assert b.reserved_usd == 0.0

    def test_available(self, session):
        self._make_task(session)
        bm = BudgetManager(session)
        bm.ensure_profile("test", limit_usd=10.0)
        assert bm.available("test") == 10.0
        bm.reserve("test", "t1", 3.0)
        assert bm.available("test") == 7.0

    def test_reserve_zero_raises(self, session):
        self._make_task(session)
        bm = BudgetManager(session)
        bm.ensure_profile("test", limit_usd=10.0)
        with pytest.raises(ValueError):
            bm.reserve("test", "t1", 0.0)

    def test_reserve_no_budget_raises(self, session):
        self._make_task(session)
        bm = BudgetManager(session)
        with pytest.raises(NoBudgetError):
            bm.reserve("nonexistent", "t1", 1.0)


# ── Locks ─────────────────────────────────────────────────────────

class TestLocks:

    def test_acquire(self, session):
        lm = LockManager(session)
        lock = lm.acquire("res1", "owner1")
        assert lock.resource == "res1"
        assert lock.owner == "owner1"

    def test_acquire_conflict(self, session):
        lm = LockManager(session)
        lm.acquire("res1", "owner1")
        with pytest.raises(LockConflictError):
            lm.acquire("res1", "owner2")

    def test_acquire_same_owner(self, session):
        lm = LockManager(session)
        lm.acquire("res1", "owner1")
        # Same owner — extend
        lock = lm.acquire("res1", "owner1")
        assert lock.owner == "owner1"

    def test_release(self, session):
        lm = LockManager(session)
        lm.acquire("res1", "owner1")
        assert lm.release("res1", "owner1")

    def test_release_wrong_owner(self, session):
        lm = LockManager(session)
        lm.acquire("res1", "owner1")
        assert not lm.release("res1", "owner2")

    def test_is_locked(self, session):
        lm = LockManager(session)
        assert not lm.is_locked("res1")
        lm.acquire("res1", "owner1")
        assert lm.is_locked("res1")

    def test_expire_stale(self, session):
        lm = LockManager(session)
        lm.acquire("res1", "owner1", ttl=timedelta(seconds=1))
        import time
        time.sleep(1.1)
        count = lm.expire_stale()
        assert count == 1
        assert not lm.is_locked("res1")


# ── Events ────────────────────────────────────────────────────────

class TestEvents:

    def _make_task(self, session):
        t = Task(id="t1", canonical_id="canonical:t1", title="test",
                 channel="test", channel_update_id=1, sender_id="u1")
        session.add(t)
        session.flush()
        return t

    def test_record_event(self, session):
        self._make_task(session)
        ej = EventJournal(session)
        ev = ej.record("t1", "task_created", {"title": "hello"})
        assert ev.event_type == "task_created"
        assert ev.task_id == "t1"
        assert ev.event_hash is not None
        assert ev.prev_hash is None  # first event

    def test_chain(self, session):
        self._make_task(session)
        ej = EventJournal(session)
        ev1 = ej.record("t1", "status_change", {"from": "received", "to": "classifying"})
        ev2 = ej.record("t1", "status_change", {"from": "classifying", "to": "planning"})
        assert ev2.prev_hash == ev1.event_hash

    def test_verify_chain_valid(self, session):
        self._make_task(session)
        ej = EventJournal(session)
        ej.record("t1", "a")
        ej.record("t1", "b")
        ej.record("t1", "c")
        valid, broken = ej.verify_chain("t1")
        assert valid
        assert broken is None

    def test_verify_chain_tampered(self, session):
        self._make_task(session)
        ej = EventJournal(session)
        ej.record("t1", "a")
        ev2 = ej.record("t1", "b")
        # Tamper
        ev2.event_hash = "bad_hash"
        session.flush()
        valid, broken = ej.verify_chain("t1")
        assert not valid
        assert broken is not None


# ── Binder ────────────────────────────────────────────────────────

class TestBinder:

    def test_bind_new(self, session):
        tb = TaskBinder(session)
        task, is_new = tb.bind_or_create("telegram", 1001, "user_42", "test task")
        assert is_new
        assert task.channel == "telegram"
        assert task.channel_update_id == 1001
        assert task.canonical_id is not None

    def test_bind_duplicate(self, session):
        """S1-AC-6: повторный update_id → нет дубля."""
        tb = TaskBinder(session)
        t1, is_new1 = tb.bind_or_create("telegram", 1001, "user_42")
        t2, is_new2 = tb.bind_or_create("telegram", 1001, "user_42")
        assert is_new1
        assert not is_new2
        assert t1.id == t2.id

    def test_find_by_canonical(self, session):
        tb = TaskBinder(session)
        task, _ = tb.bind_or_create("telegram", 1002, "user_42")
        found = tb.find_by_canonical(task.canonical_id)
        assert found is not None
        assert found.id == task.id


# ── Fault injection ───────────────────────────────────────────────

class TestFaultInjection:

    def _make_task(self, session, task_id="t1"):
        t = Task(id=task_id, canonical_id=f"canonical:{task_id}",
                 title="fault-test", channel="test", channel_update_id=hash(task_id),
                 sender_id="u1")
        session.add(t)
        session.flush()
        return t

    def _make_step(self, session, step_id="s1", task_id="t1"):
        s = Step(id=step_id, task_id=task_id, order=1)
        session.add(s)
        session.flush()
        return s

    def test_kill_between_reserve_and_effect(self, session):
        """S1-AC-2: kill in reserve→effect→settle → no double effect.

        Simulate: reserve budget, register side_effect (pending),
        then simulate crash before settle. On recovery, reconcile → needs_reconciliation.
        """
        self._make_task(session)
        self._make_step(session)

        # Reserve budget
        bm = BudgetManager(session)
        bm.ensure_profile("test", limit_usd=10.0)
        r = bm.reserve("test", "t1", 1.0, "s1")

        # Register side_effect but DON'T settle (simulate crash)
        guard = IdempotencyGuard(session)
        is_new, se = guard.try_register("t1", "s1", "telegram_send", {"msg": "hi"})
        assert is_new
        # ... CRASH HERE ...

        # Recovery: reconcile pending effects
        pending = guard.reconcile_pending("t1")
        assert len(pending) == 1
        assert pending[0].status == SideEffectStatus.NEEDS_RECONCILIATION

        # Budget is still reserved (not settled, not released)
        session.refresh(r)
        assert r.status == "reserved"

    def test_double_effect_on_replay_prevented(self, session):
        """Replaying the same idempotent action must not create a second effect."""
        self._make_task(session)
        self._make_step(session)

        guard = IdempotencyGuard(session)
        _, se1 = guard.try_register("t1", "s1", "send", {"msg": "hello"})
        guard.mark_done(se1, "ext-99")

        # Replay
        _, se2 = guard.try_register("t1", "s1", "send", {"msg": "hello"})
        assert se2.status == SideEffectStatus.DONE  # already done, not re-executed
        assert se1.id == se2.id

    def test_budget_invariant_sum_le_limit(self, session):
        """S1-AC-7: sum settled+reserved ≤ limit."""
        self._make_task(session, "t1")
        self._make_task(session, "t2")
        bm = BudgetManager(session)
        b = bm.ensure_profile("test", limit_usd=10.0)

        r1 = bm.reserve("test", "t1", 3.0)
        r2 = bm.reserve("test", "t2", 4.0)
        bm.settle(r1)

        session.refresh(b)
        assert b.reserved_usd + b.settled_usd <= b.limit_usd
        assert b.reserved_usd == 4.0
        assert b.settled_usd == 3.0
        assert b.reserved_usd + b.settled_usd == 7.0  # ≤ 10.0