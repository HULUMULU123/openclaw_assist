"""Task Core — Idempotency guard (S1-T3).

Every external side effect is guarded by an idempotency key:
    key = hash(task_id, step_id, effect_type, canonical_args)

On restart, pending side effects without confirmation → needs_reconciliation,
NOT automatic retry (per FR-014).
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    IdempotencyKey, SideEffect, SideEffectStatus, Task,
)


def compute_idempotency_key(
    task_id: str,
    step_id: str,
    effect_type: str,
    canonical_args: dict,
) -> str:
    """Compute deterministic idempotency key.

    canonical_args must have sorted keys for deterministic hashing.
    """
    payload = json.dumps({
        "task_id": task_id,
        "step_id": step_id,
        "effect_type": effect_type,
        "args": canonical_args,
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


class IdempotencyGuard:
    """Ensures at-most-once external effect execution."""

    def __init__(self, session: Session):
        self.session = session

    def try_register(
        self,
        task_id: str,
        step_id: str,
        effect_type: str,
        canonical_args: dict,
    ) -> Tuple[bool, Optional[SideEffect]]:
        """Atomically register a pending side effect.

        Returns (is_new, side_effect).
        If the key already exists, returns (False, existing_side_effect).
        """
        key = compute_idempotency_key(task_id, step_id, effect_type, canonical_args)

        # Check if already registered
        existing = self.session.scalar(
            select(IdempotencyKey).where(IdempotencyKey.key == key)
        )
        if existing is not None:
            se = self.session.scalar(
                select(SideEffect).where(SideEffect.idempotency_key == key)
            )
            return False, se

        # Create idempotency key + side effect in one atomic block
        canonical_json = json.dumps(canonical_args, sort_keys=True, ensure_ascii=False)

        ik = IdempotencyKey(
            key=key,
            task_id=task_id,
            step_id=step_id,
            effect_type=effect_type,
        )
        self.session.add(ik)

        se = SideEffect(
            task_id=task_id,
            step_id=step_id,
            effect_type=effect_type,
            canonical_args=canonical_json,
            idempotency_key=key,
            status=SideEffectStatus.PENDING,
        )
        self.session.add(se)
        self.session.flush()

        return True, se

    def mark_done(self, side_effect: SideEffect, external_id: str,
                  result: Optional[dict] = None) -> None:
        side_effect.status = SideEffectStatus.DONE
        side_effect.external_id = external_id
        side_effect.result_json = json.dumps(result) if result else None
        side_effect.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, side_effect: SideEffect,
                    error: Optional[str] = None) -> None:
        side_effect.status = SideEffectStatus.FAILED
        side_effect.result_json = json.dumps({"error": error}) if error else None
        side_effect.completed_at = datetime.now(timezone.utc)

    def reconcile_pending(self, task_id: str) -> list[SideEffect]:
        """Find all pending side effects for a task and mark them
        as needs_reconciliation. Called on restart/recovery."""
        pending = self.session.scalars(
            select(SideEffect).where(
                SideEffect.task_id == task_id,
                SideEffect.status == SideEffectStatus.PENDING,
            )
        ).all()

        for se in pending:
            se.status = SideEffectStatus.NEEDS_RECONCILIATION

        self.session.flush()
        return list(pending)