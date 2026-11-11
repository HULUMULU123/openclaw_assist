"""Task Core — Budget manager with CAS reservation (S1-T5)."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .models import Budget, BudgetReservation


class BudgetExceededError(ValueError):
    """Raised when reservation would exceed budget limit."""
    def __init__(self, profile: str, limit: float, would_be: float):
        super().__init__(
            f"Budget '{profile}': {would_be:.4f} would exceed limit {limit:.4f}")
        self.profile = profile
        self.limit = limit
        self.would_be = would_be


class NoBudgetError(ValueError):
    """Raised when no budget profile exists."""
    def __init__(self, profile: str):
        super().__init__(f"Budget profile not found: {profile}")
        self.profile = profile


class BudgetManager:
    """CAS-based budget reservation.

    reserve → settle/release. All mutations are atomic CAS to prevent
    overspend under concurrency (S1-AC-4).
    """

    def __init__(self, session: Session):
        self.session = session

    def ensure_profile(self, profile: str, limit_usd: float,
                       period: Optional[str] = None) -> Budget:
        """Get or create a budget profile."""
        b = self.session.scalar(
            select(Budget).where(Budget.profile == profile)
        )
        if b is None:
            b = Budget(profile=profile, limit_usd=limit_usd, period=period)
            self.session.add(b)
            self.session.flush()
        return b

    def reserve(self, profile: str, task_id: str, amount_usd: float,
                step_id: Optional[str] = None) -> BudgetReservation:
        """Atomically reserve budget.

        Uses UPDATE ... WHERE reserved_usd + amount <= limit_usd (CAS).
        Raises BudgetExceededError if reservation would exceed the limit.
        """
        if amount_usd <= 0:
            raise ValueError("amount_usd must be positive")

        budget = self.session.scalar(
            select(Budget).where(Budget.profile == profile)
        )
        if budget is None:
            raise NoBudgetError(profile)

        # CAS: atomically increment reserved_usd if within limit
        result = self.session.execute(
            update(Budget)
            .where(
                Budget.id == budget.id,
                Budget.reserved_usd + amount_usd <= Budget.limit_usd,
            )
            .values(reserved_usd=Budget.reserved_usd + amount_usd)
        )

        if result.rowcount == 0:
            # CAS failed — would exceed limit
            current = budget.reserved_usd
            raise BudgetExceededError(profile, budget.limit_usd, current + amount_usd)

        # Refresh to get updated value
        self.session.refresh(budget)

        reservation = BudgetReservation(
            budget_id=budget.id,
            task_id=task_id,
            step_id=step_id,
            amount_usd=amount_usd,
            status="reserved",
        )
        self.session.add(reservation)
        self.session.flush()
        return reservation

    def settle(self, reservation: BudgetReservation) -> None:
        """Settle a reservation — move from reserved to settled."""
        if reservation.status != "reserved":
            raise ValueError(f"Cannot settle reservation with status '{reservation.status}'")

        budget = self.session.scalar(
            select(Budget).where(Budget.id == reservation.budget_id)
        )
        if budget is None:
            raise NoBudgetError(reservation.budget_id)

        # CAS: move from reserved to settled
        result = self.session.execute(
            update(Budget)
            .where(
                Budget.id == budget.id,
                Budget.reserved_usd >= reservation.amount_usd,
            )
            .values(
                reserved_usd=Budget.reserved_usd - reservation.amount_usd,
                settled_usd=Budget.settled_usd + reservation.amount_usd,
            )
        )

        if result.rowcount == 0:
            raise RuntimeError("CAS settle failed — concurrent modification?")

        reservation.status = "settled"
        reservation.settled_at = datetime.now(timezone.utc)
        self.session.flush()

    def release(self, reservation: BudgetReservation) -> None:
        """Release a reservation without settling."""
        if reservation.status != "reserved":
            raise ValueError(f"Cannot release reservation with status '{reservation.status}'")

        budget = self.session.scalar(
            select(Budget).where(Budget.id == reservation.budget_id)
        )
        if budget is None:
            raise NoBudgetError(reservation.budget_id)

        # CAS: release back to available
        result = self.session.execute(
            update(Budget)
            .where(
                Budget.id == budget.id,
                Budget.reserved_usd >= reservation.amount_usd,
            )
            .values(reserved_usd=Budget.reserved_usd - reservation.amount_usd)
        )

        if result.rowcount == 0:
            raise RuntimeError("CAS release failed — concurrent modification?")

        reservation.status = "released"
        reservation.settled_at = datetime.now(timezone.utc)
        self.session.flush()

    def available(self, profile: str) -> float:
        """Return available (unreserved) budget."""
        budget = self.session.scalar(
            select(Budget).where(Budget.profile == profile)
        )
        if budget is None:
            return 0.0
        return budget.limit_usd - budget.reserved_usd