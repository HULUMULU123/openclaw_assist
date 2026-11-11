"""Task Core — Status machines with transition validation (S1-T2)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, FrozenSet, Optional, Set

from .models import (
    TaskStatus, StepStatus, ApprovalStatus, JobStatus, SideEffectStatus,
)


@dataclass(frozen=True)
class Transition:
    source: str
    target: str


# ── Task transitions ──────────────────────────────────────────────

TASK_TRANSITIONS: FrozenSet[Transition] = frozenset({
    Transition(TaskStatus.RECEIVED, TaskStatus.CLASSIFYING),
    Transition(TaskStatus.CLASSIFYING, TaskStatus.NEEDS_USER_INPUT),
    Transition(TaskStatus.CLASSIFYING, TaskStatus.PLANNING),
    Transition(TaskStatus.CLASSIFYING, TaskStatus.FAILED),
    Transition(TaskStatus.NEEDS_USER_INPUT, TaskStatus.PLANNING),
    Transition(TaskStatus.NEEDS_USER_INPUT, TaskStatus.CANCELLED),
    Transition(TaskStatus.PLANNING, TaskStatus.AWAITING_APPROVAL),
    Transition(TaskStatus.PLANNING, TaskStatus.FAILED),
    Transition(TaskStatus.AWAITING_APPROVAL, TaskStatus.RUNNING),
    Transition(TaskStatus.AWAITING_APPROVAL, TaskStatus.CANCELLED),
    Transition(TaskStatus.AWAITING_APPROVAL, TaskStatus.FAILED),
    Transition(TaskStatus.RUNNING, TaskStatus.VERIFYING),
    Transition(TaskStatus.RUNNING, TaskStatus.PAUSED),
    Transition(TaskStatus.RUNNING, TaskStatus.FAILED),
    Transition(TaskStatus.RUNNING, TaskStatus.BLOCKED_BUDGET),
    Transition(TaskStatus.RUNNING, TaskStatus.BLOCKED_MODEL_UNAVAILABLE),
    Transition(TaskStatus.RUNNING, TaskStatus.BLOCKED_POLICY),
    Transition(TaskStatus.RUNNING, TaskStatus.BLOCKED_GUI_UNAVAILABLE),
    Transition(TaskStatus.RUNNING, TaskStatus.BLOCKED_RESOURCE),
    Transition(TaskStatus.RUNNING, TaskStatus.NEEDS_LOGIN),
    Transition(TaskStatus.PAUSED, TaskStatus.RUNNING),
    Transition(TaskStatus.PAUSED, TaskStatus.CANCELLED),
    Transition(TaskStatus.VERIFYING, TaskStatus.SUCCEEDED),
    Transition(TaskStatus.VERIFYING, TaskStatus.FAILED),
    Transition(TaskStatus.VERIFYING, TaskStatus.RUNNING),  # retry
    Transition(TaskStatus.BLOCKED_BUDGET, TaskStatus.PLANNING),
    Transition(TaskStatus.BLOCKED_MODEL_UNAVAILABLE, TaskStatus.PLANNING),
    Transition(TaskStatus.BLOCKED_POLICY, TaskStatus.PLANNING),
    Transition(TaskStatus.BLOCKED_GUI_UNAVAILABLE, TaskStatus.PLANNING),
    Transition(TaskStatus.BLOCKED_RESOURCE, TaskStatus.PLANNING),
    Transition(TaskStatus.NEEDS_LOGIN, TaskStatus.PLANNING),
})

# Terminal states (no outgoing transitions)
TASK_TERMINAL: FrozenSet[TaskStatus] = frozenset({
    TaskStatus.SUCCEEDED,
    TaskStatus.FAILED,
    TaskStatus.CANCELLED,
})

# States that can transition on their own (timeout/event-driven)
TASK_AUTO_TRANSITIONS: Dict[TaskStatus, TaskStatus] = {
    # After TTL: pending approval → expired → back to planning
}


# ── Step transitions ──────────────────────────────────────────────

STEP_TRANSITIONS: FrozenSet[Transition] = frozenset({
    Transition(StepStatus.PENDING, StepStatus.READY),
    Transition(StepStatus.PENDING, StepStatus.SKIPPED),
    Transition(StepStatus.READY, StepStatus.RUNNING),
    Transition(StepStatus.READY, StepStatus.SKIPPED),
    Transition(StepStatus.RUNNING, StepStatus.VERIFYING),
    Transition(StepStatus.RUNNING, StepStatus.FAILED),
    Transition(StepStatus.VERIFYING, StepStatus.SUCCEEDED),
    Transition(StepStatus.VERIFYING, StepStatus.FAILED),
    Transition(StepStatus.VERIFYING, StepStatus.NEEDS_EVIDENCE),
    Transition(StepStatus.VERIFYING, StepStatus.RUNNING),  # retry
    Transition(StepStatus.FAILED, StepStatus.READY),       # retry
    Transition(StepStatus.NEEDS_EVIDENCE, StepStatus.VERIFYING),
    Transition(StepStatus.PENDING, StepStatus.NEEDS_RECONCILIATION),
    Transition(StepStatus.READY, StepStatus.NEEDS_RECONCILIATION),
    Transition(StepStatus.RUNNING, StepStatus.NEEDS_RECONCILIATION),
})

STEP_TERMINAL: FrozenSet[StepStatus] = frozenset({
    StepStatus.SUCCEEDED,
    StepStatus.SKIPPED,
})


# ── Approval transitions ──────────────────────────────────────────

APPROVAL_TRANSITIONS: FrozenSet[Transition] = frozenset({
    Transition(ApprovalStatus.PENDING, ApprovalStatus.APPROVED),
    Transition(ApprovalStatus.PENDING, ApprovalStatus.REJECTED),
    Transition(ApprovalStatus.PENDING, ApprovalStatus.EXPIRED),
    Transition(ApprovalStatus.PENDING, ApprovalStatus.INVALIDATED),
})

APPROVAL_TERMINAL: FrozenSet[ApprovalStatus] = frozenset({
    ApprovalStatus.APPROVED,
    ApprovalStatus.REJECTED,
    ApprovalStatus.EXPIRED,
    ApprovalStatus.INVALIDATED,
})


# ── Job transitions ───────────────────────────────────────────────

JOB_TRANSITIONS: FrozenSet[Transition] = frozenset({
    Transition(JobStatus.QUEUED, JobStatus.LEASED),
    Transition(JobStatus.LEASED, JobStatus.RUNNING),
    Transition(JobStatus.LEASED, JobStatus.EXPIRED),
    Transition(JobStatus.LEASED, JobStatus.QUEUED),  # lease expired, re-queue
    Transition(JobStatus.RUNNING, JobStatus.DONE),
    Transition(JobStatus.RUNNING, JobStatus.FAILED),
    Transition(JobStatus.RUNNING, JobStatus.QUEUED),  # retry
    Transition(JobStatus.FAILED, JobStatus.QUEUED),   # retry
})

JOB_TERMINAL: FrozenSet[JobStatus] = frozenset({
    JobStatus.DONE,
    JobStatus.EXPIRED,
})


# ── SideEffect transitions ────────────────────────────────────────

SIDE_EFFECT_TRANSITIONS: FrozenSet[Transition] = frozenset({
    Transition(SideEffectStatus.PENDING, SideEffectStatus.DONE),
    Transition(SideEffectStatus.PENDING, SideEffectStatus.FAILED),
    Transition(SideEffectStatus.PENDING, SideEffectStatus.NEEDS_RECONCILIATION),
    Transition(SideEffectStatus.NEEDS_RECONCILIATION, SideEffectStatus.DONE),
    Transition(SideEffectStatus.NEEDS_RECONCILIATION, SideEffectStatus.FAILED),
})

SIDE_EFFECT_TERMINAL: FrozenSet[SideEffectStatus] = frozenset({
    SideEffectStatus.DONE,
    SideEffectStatus.FAILED,
})


# ── Transition engine ─────────────────────────────────────────────

class InvalidTransitionError(ValueError):
    """Raised when a status transition is not allowed."""
    def __init__(self, current: str, target: str, entity: str):
        super().__init__(
            f"Invalid transition for {entity}: '{current}' → '{target}'")
        self.current = current
        self.target = target
        self.entity = entity


class StatusMachine:
    """Validates and records status transitions."""

    TRANSITIONS: Dict[str, FrozenSet[Transition]] = {
        "task": TASK_TRANSITIONS,
        "step": STEP_TRANSITIONS,
        "approval": APPROVAL_TRANSITIONS,
        "job": JOB_TRANSITIONS,
        "side_effect": SIDE_EFFECT_TRANSITIONS,
    }

    TERMINAL: Dict[str, FrozenSet] = {
        "task": TASK_TERMINAL,
        "step": STEP_TERMINAL,
        "approval": APPROVAL_TERMINAL,
        "job": JOB_TERMINAL,
        "side_effect": SIDE_EFFECT_TERMINAL,
    }

    @classmethod
    def validate(cls, entity: str, current: str, target: str) -> None:
        """Raise InvalidTransitionError if transition is not allowed."""
        transitions = cls.TRANSITIONS.get(entity)
        if transitions is None:
            raise ValueError(f"Unknown entity: {entity}")

        t = Transition(current, target)
        if t not in transitions:
            raise InvalidTransitionError(current, target, entity)

    @classmethod
    def is_valid(cls, entity: str, current: str, target: str) -> bool:
        try:
            cls.validate(entity, current, target)
            return True
        except InvalidTransitionError:
            return False

    @classmethod
    def is_terminal(cls, entity: str, status: str) -> bool:
        terminal_set = cls.TERMINAL.get(entity)
        if terminal_set is None:
            return False
        return status in terminal_set

    @classmethod
    def allowed_targets(cls, entity: str, current: str) -> Set[str]:
        transitions = cls.TRANSITIONS.get(entity, frozenset())
        return {t.target for t in transitions if t.source == current}