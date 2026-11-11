"""Task Core — Pydantic schemas for API and validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .models import (
    TaskStatus, StepStatus, ApprovalStatus, JobStatus, SideEffectStatus,
    DataClass,
)


# ── Task ──────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    channel: str = Field(..., max_length=32)
    update_id: int
    sender_id: str = Field(..., max_length=128)
    title: Optional[str] = None
    description: Optional[str] = None
    data_class: DataClass = DataClass.PRIVATE
    priority: int = 0


class TaskResponse(BaseModel):
    id: str
    canonical_id: str
    status: TaskStatus
    title: Optional[str]
    channel: Optional[str]
    sender_id: Optional[str]
    data_class: DataClass
    priority: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class TaskTransition(BaseModel):
    target: TaskStatus
    reason: Optional[str] = None


# ── Step ──────────────────────────────────────────────────────────

class StepCreate(BaseModel):
    task_id: str
    order: int
    objective: Optional[str] = None
    allowed_tools: Optional[list[str]] = None
    budget_usd: Optional[float] = None
    deadline: Optional[datetime] = None


class StepResponse(BaseModel):
    id: str
    task_id: str
    order: int
    status: StepStatus
    objective: Optional[str]
    budget_usd: Optional[float]
    deadline: Optional[datetime]
    result_json: Optional[str]
    cost_usd: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StepTransition(BaseModel):
    target: StepStatus
    reason: Optional[str] = None


# ── Job ───────────────────────────────────────────────────────────

class JobAcquire(BaseModel):
    step_id: str
    worker_id: str = Field(..., max_length=128)


class JobResponse(BaseModel):
    id: str
    step_id: str
    status: JobStatus
    worker_id: Optional[str]
    attempt: int
    max_attempts: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Approval ──────────────────────────────────────────────────────

class ApprovalResponse(BaseModel):
    id: str
    task_id: str
    subject: str
    status: ApprovalStatus
    plan_hash: Optional[str]
    expires_at: Optional[datetime]
    decided_at: Optional[datetime]
    decided_by: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected|invalidated)$")
    decided_by: str = Field(..., max_length=128)
    reason: Optional[str] = None


# ── Side effect ───────────────────────────────────────────────────

class SideEffectCreate(BaseModel):
    task_id: str
    step_id: str
    effect_type: str = Field(..., max_length=64)
    canonical_args: dict


class SideEffectResponse(BaseModel):
    id: str
    task_id: str
    step_id: Optional[str]
    effect_type: str
    status: SideEffectStatus
    idempotency_key: str
    external_id: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── Budget ────────────────────────────────────────────────────────

class BudgetReserveRequest(BaseModel):
    profile: str = Field(..., max_length=64)
    task_id: str
    step_id: Optional[str] = None
    amount_usd: float = Field(..., gt=0)


class BudgetResponse(BaseModel):
    profile: str
    limit_usd: float
    reserved_usd: float
    settled_usd: float
    available_usd: float

    model_config = {"from_attributes": True}


# ── Lock ──────────────────────────────────────────────────────────

class LockRequest(BaseModel):
    resource: str = Field(..., max_length=256)
    owner: str = Field(..., max_length=128)
    ttl_seconds: int = Field(default=300, ge=1, le=3600)


class LockResponse(BaseModel):
    resource: str
    owner: str
    ttl_seconds: int
    acquired_at: datetime

    model_config = {"from_attributes": True}


# ── Event ─────────────────────────────────────────────────────────

class EventResponse(BaseModel):
    id: int
    task_id: str
    step_id: Optional[str]
    event_type: str
    payload: Optional[str]
    prev_hash: Optional[str]
    event_hash: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}