"""Task Core — SQLAlchemy ORM models (17 tables per ADR-001)."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Enum,
    create_engine, event
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── Enums ────────────────────────────────────────────────────────

class TaskStatus(str, PyEnum):
    RECEIVED = "received"
    CLASSIFYING = "classifying"
    NEEDS_USER_INPUT = "needs_user_input"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    RUNNING = "running"
    VERIFYING = "verifying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    BLOCKED_BUDGET = "blocked_budget"
    BLOCKED_MODEL_UNAVAILABLE = "blocked_model_unavailable"
    BLOCKED_POLICY = "blocked_policy"
    BLOCKED_GUI_UNAVAILABLE = "blocked_gui_unavailable"
    BLOCKED_RESOURCE = "blocked_resource"
    NEEDS_LOGIN = "needs_login"


class StepStatus(str, PyEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    VERIFYING = "verifying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    NEEDS_EVIDENCE = "needs_evidence"
    NEEDS_RECONCILIATION = "needs_reconciliation"
    SKIPPED = "skipped"


class ApprovalStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"


class JobStatus(str, PyEnum):
    QUEUED = "queued"
    LEASED = "leased"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    EXPIRED = "expired"


class SideEffectStatus(str, PyEnum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    NEEDS_RECONCILIATION = "needs_reconciliation"


class DataClass(str, PyEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    LOCAL_ONLY = "local_only"
    SECRET = "secret"


# ── Models ────────────────────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id: Mapped[Optional[str]] = mapped_column(String(256))
    canonical_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.RECEIVED, nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    data_class: Mapped[DataClass] = mapped_column(
        Enum(DataClass), default=DataClass.PRIVATE, nullable=False)
    channel: Mapped[Optional[str]] = mapped_column(String(32))
    channel_update_id: Mapped[Optional[int]] = mapped_column(Integer)
    sender_id: Mapped[Optional[str]] = mapped_column(String(128))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    messages: Mapped[list["TaskMessage"]] = relationship(
        back_populates="task", cascade="all, delete-orphan")
    steps: Mapped[list["Step"]] = relationship(
        back_populates="task", cascade="all, delete-orphan")
    approvals: Mapped[list["Approval"]] = relationship(
        back_populates="task", cascade="all, delete-orphan")
    artifacts: Mapped[list["Artifact"]] = relationship(
        back_populates="task", cascade="all, delete-orphan")
    events: Mapped[list["Event"]] = relationship(
        back_populates="task", cascade="all, delete-orphan")
    side_effects: Mapped[list["SideEffect"]] = relationship(
        back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tasks_status_created", "status", "created_at"),
    )


class TaskMessage(Base):
    __tablename__ = "task_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # user | assistant | system
    content: Mapped[Optional[str]] = mapped_column(Text)
    data_class: Mapped[DataClass] = mapped_column(
        Enum(DataClass), default=DataClass.PRIVATE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="messages")
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tm_task_created", "task_id", "created_at"),
    )


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id: Mapped[str] = mapped_column(
        ForeignKey("task_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)  # photo | voice | document | ...
    mime_type: Mapped[Optional[str]] = mapped_column(String(128))
    sha256: Mapped[Optional[str]] = mapped_column(String(64))
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    storage_path: Mapped[Optional[str]] = mapped_column(Text)
    data_class: Mapped[DataClass] = mapped_column(
        Enum(DataClass), default=DataClass.PRIVATE, nullable=False)

    message: Mapped["TaskMessage"] = relationship(back_populates="attachments")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, unique=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    versions: Mapped[list["PlanVersion"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan")


class PlanVersion(Base):
    __tablename__ = "plan_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # JSON plan
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    plan: Mapped["Plan"] = relationship(back_populates="versions")

    __table_args__ = (
        UniqueConstraint("plan_id", "version", name="uq_plan_version"),
    )


class Step(Base):
    __tablename__ = "steps"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StepStatus] = mapped_column(
        Enum(StepStatus), default=StepStatus.PENDING, nullable=False, index=True)
    objective: Mapped[Optional[str]] = mapped_column(Text)
    allowed_tools: Mapped[Optional[str]] = mapped_column(Text)  # JSON list
    budget_usd: Mapped[Optional[float]] = mapped_column(Float)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime)
    result_json: Mapped[Optional[str]] = mapped_column(Text)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="steps")
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="step", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    step_id: Mapped[str] = mapped_column(
        ForeignKey("steps.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.QUEUED, nullable=False, index=True)
    worker_id: Mapped[Optional[str]] = mapped_column(String(128))
    lease_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    result_json: Mapped[Optional[str]] = mapped_column(Text)
    error_json: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    step: Mapped["Step"] = relationship(back_populates="jobs")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    plan_hash: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    decided_by: Mapped[Optional[str]] = mapped_column(String(128))
    decision_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="approvals")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("steps.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)  # file | text | url | json
    mime_type: Mapped[Optional[str]] = mapped_column(String(128))
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    sha256: Mapped[Optional[str]] = mapped_column(String(64))
    storage_path: Mapped[Optional[str]] = mapped_column(Text)
    content_text: Mapped[Optional[str]] = mapped_column(Text)
    data_class: Mapped[DataClass] = mapped_column(
        Enum(DataClass), default=DataClass.PRIVATE, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="artifacts")


class Event(Base):
    """Append-only event journal."""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id: Mapped[Optional[str]] = mapped_column(String(36))
    trace_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    prev_hash: Mapped[Optional[str]] = mapped_column(String(64))
    event_hash: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_events_task_type", "task_id", "event_type"),
        Index("ix_events_trace", "trace_id", "created_at"),
    )


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    limit_usd: Mapped[float] = mapped_column(Float, nullable=False)
    reserved_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    settled_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    period: Mapped[Optional[str]] = mapped_column(String(16))  # daily | task | total
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("reserved_usd >= 0", name="ck_budget_reserved_nonneg"),
        CheckConstraint("settled_usd >= 0", name="ck_budget_settled_nonneg"),
    )


class BudgetReservation(Base):
    __tablename__ = "budget_reservations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    budget_id: Mapped[str] = mapped_column(
        ForeignKey("budgets.id"), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id: Mapped[Optional[str]] = mapped_column(String(36))
    amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default="reserved", nullable=False)  # reserved | settled | released
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        CheckConstraint("amount_usd > 0", name="ck_budget_reservation_positive"),
    )


class SideEffect(Base):
    """Inventory of external actions."""
    __tablename__ = "side_effects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id: Mapped[Optional[str]] = mapped_column(String(36))
    effect_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_args: Mapped[str] = mapped_column(Text, nullable=False)  # JSON, sorted keys
    idempotency_key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True)
    status: Mapped[SideEffectStatus] = mapped_column(
        Enum(SideEffectStatus), default=SideEffectStatus.PENDING, nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(256))
    result_json: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    task: Mapped["Task"] = relationship(back_populates="side_effects")

    __table_args__ = (
        Index("ix_se_task_status", "task_id", "status"),
    )


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(
        String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id: Mapped[Optional[str]] = mapped_column(String(36))
    effect_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class PolicyApplied(Base):
    __tablename__ = "policies_applied"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)  # allow | deny | require_approval
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class ModelCall(Base):
    __tablename__ = "model_calls"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id: Mapped[Optional[str]] = mapped_column(String(36))
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    api_model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    tokens_in: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    latency_s: Mapped[Optional[float]] = mapped_column(Float)
    outcome: Mapped[Optional[str]] = mapped_column(String(32))  # success | error | timeout
    schema_ver: Mapped[Optional[str]] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_mc_task_provider", "task_id", "provider"),
    )


class Lock(Base):
    __tablename__ = "locks"

    resource: Mapped[str] = mapped_column(String(256), primary_key=True)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    ttl_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False)


class PolicyDecision(Base):
    __tablename__ = "policy_decisions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


# ── Engine helper ─────────────────────────────────────────────────

def create_db_engine(db_path: str = "sqlite:///data/taskcore.db"):
    engine = create_engine(db_path, echo=False)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine