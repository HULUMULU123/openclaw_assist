"""Task Core — Append-only event journal with hash chain (S1-T7)."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Event, Task


class EventJournal:
    """Append-only event log with hash-chaining for tamper detection."""

    def __init__(self, session: Session):
        self.session = session

    def record(self, task_id: str, event_type: str,
               payload: Optional[dict] = None,
               step_id: Optional[str] = None,
               trace_id: Optional[str] = None) -> Event:
        """Record a new event, chained to the previous one for this task."""

        # Get the last event for this task to chain
        last_event = self.session.scalar(
            select(Event)
            .where(Event.task_id == task_id)
            .order_by(Event.id.desc())
            .limit(1)
        )

        prev_hash = last_event.event_hash if last_event else None

        # Compute event hash
        payload_json = json.dumps(payload, sort_keys=True) if payload else "{}"
        hash_input = f"{task_id}:{event_type}:{payload_json}:{prev_hash or ''}"
        event_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        event = Event(
            task_id=task_id,
            step_id=step_id,
            trace_id=trace_id,
            event_type=event_type,
            payload=payload_json if payload else None,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def verify_chain(self, task_id: str) -> tuple[bool, Optional[int]]:
        """Verify the hash chain for a task's events.

        Returns (is_valid, first_broken_event_id).
        """
        events = self.session.scalars(
            select(Event)
            .where(Event.task_id == task_id)
            .order_by(Event.id.asc())
        ).all()

        prev_hash = None
        for ev in events:
            payload_json = ev.payload or "{}"
            expected = hashlib.sha256(
                f"{ev.task_id}:{ev.event_type}:{payload_json}:{prev_hash or ''}".encode()
            ).hexdigest()
            if expected != ev.event_hash:
                return False, ev.id
            prev_hash = ev.event_hash

        return True, None