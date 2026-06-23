from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import ClassVar
from uuid import UUID, uuid4


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── Base ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events.
    frozen=True makes events immutable after construction — intentional.
    """
    event_id:       UUID     = field(default_factory=uuid4)
    occurred_at:    datetime = field(default_factory=_now)
    correlation_id: UUID | None = field(default=None)
    causation_id:   UUID | None = field(default=None)

    # Subclasses declare this so the event store knows what string to persist
    event_type: ClassVar[str]

    def to_dict(self) -> dict:
        """Serialise payload fields (excluding base audit fields)."""
        raise NotImplementedError


# ─── Account events ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AccountOpened(DomainEvent):
    event_type: ClassVar[str] = "AccountOpened"

    account_id: UUID    = field(default_factory=uuid4)
    owner_name: str     = ""
    initial_balance: Decimal = Decimal("0.00")
    currency:   str     = "USD"

    def to_dict(self) -> dict:
        return {
            "account_id":      str(self.account_id),
            "owner_name":      self.owner_name,
            "initial_balance": str(self.initial_balance),
            "currency":        self.currency,
        }


@dataclass(frozen=True)
class MoneyDeposited(DomainEvent):
    event_type: ClassVar[str] = "MoneyDeposited"

    account_id:  UUID    = field(default_factory=uuid4)
    amount:      Decimal = Decimal("0.00")
    description: str     = ""

    def to_dict(self) -> dict:
        return {
            "account_id":  str(self.account_id),
            "amount":      str(self.amount),
            "description": self.description,
        }


@dataclass(frozen=True)
class MoneyWithdrawn(DomainEvent):
    event_type: ClassVar[str] = "MoneyWithdrawn"

    account_id:  UUID    = field(default_factory=uuid4)
    amount:      Decimal = Decimal("0.00")
    description: str     = ""

    def to_dict(self) -> dict:
        return {
            "account_id":  str(self.account_id),
            "amount":      str(self.amount),
            "description": self.description,
        }


@dataclass(frozen=True)
class AccountClosed(DomainEvent):
    event_type: ClassVar[str] = "AccountClosed"

    account_id: UUID = field(default_factory=uuid4)
    reason:     str  = ""

    def to_dict(self) -> dict:
        return {
            "account_id": str(self.account_id),
            "reason":     self.reason,
        }


# ─── Registry ─────────────────────────────────────────────────────────────────
# Used by the event store to deserialise persisted rows back to typed events.

EVENT_REGISTRY: dict[str, type[DomainEvent]] = {
    "AccountOpened":  AccountOpened,
    "MoneyDeposited": MoneyDeposited,
    "MoneyWithdrawn": MoneyWithdrawn,
    "AccountClosed":  AccountClosed,
}