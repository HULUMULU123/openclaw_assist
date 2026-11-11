"""Task Core — Canonical task_id binder for multi-channel dedup (S1-T9)."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Task


class TaskBinder:
    """Maps channel-specific messages to canonical tasks.

    A single logical task may arrive through multiple channels
    (Telegram, web panel). The binder assigns a canonical task_id
    and deduplicates by channel + update_id.
    """

    def __init__(self, session: Session):
        self.session = session

    def bind_or_create(
        self,
        channel: str,
        update_id: int,
        sender_id: str,
        title: Optional[str] = None,
    ) -> tuple[Task, bool]:
        """Look up existing task by channel+update_id, or create a new one.

        Returns (task, is_new).
        """
        # Check if this message was already processed
        existing = self.session.scalar(
            select(Task).where(
                Task.channel == channel,
                Task.channel_update_id == update_id,
            )
        )
        if existing is not None:
            return existing, False

        # New task — generate canonical id
        canonical_id = _compute_canonical_id(channel, sender_id, update_id)

        task = Task(
            external_id=str(update_id),
            canonical_id=canonical_id,
            channel=channel,
            channel_update_id=update_id,
            sender_id=sender_id,
            title=title,
        )
        self.session.add(task)
        self.session.flush()
        return task, True

    def find_by_canonical(self, canonical_id: str) -> Optional[Task]:
        """Find a task by its canonical id."""
        return self.session.scalar(
            select(Task).where(Task.canonical_id == canonical_id)
        )


def _compute_canonical_id(channel: str, sender_id: str, update_id: int) -> str:
    """Deterministic canonical id for a multi-channel task."""
    payload = json.dumps({
        "channel": channel,
        "sender_id": sender_id,
        "update_id": update_id,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]