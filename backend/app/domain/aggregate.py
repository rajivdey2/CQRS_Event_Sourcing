from __future__ import annotations
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.domain.events import (
    AccountClosed,
    AccountOpened,
    DomainEvent,
    MoneyDeposited,
    MoneyWithdrawn,
)
from app.domain.exceptions import (
    AccountAlreadyClosedError,
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidAmountError,
)

if TYPE_CHECKING:
    pass

SNAPSHOT_THRESHOLD = 20   # take a snapshot every N events


class AccountAggregate:
    """
    The account aggregate is the consistency boundary for all financial
    operations.  It never talks to infrastructure — it only:
      1. Validates business rules
      2. Emits domain events via _raise()
      3. Updates in-memory state via _apply()

    The event store loads existing state by replaying saved events through
    _apply_saved(); new events go through _raise() which also queues them
    in _pending_events for the store to persist.
    """

    def __init__(self, account_id: UUID | None = None) -> None:
        self.account_id: UUID        = account_id or uuid4()
        self.owner_name: str         = ""
        self.balance:    Decimal     = Decimal("0.00")
        self.currency:   str         = "USD"
        self.status:     str         = "new"       # new | active | closed
        self.version:    int         = 0            # last persisted version
        self._pending_events: list[DomainEvent] = []

    # ── Public commands ───────────────────────────────────────────────────────

    def open(
        self,
        owner_name: str,
        initial_balance: Decimal = Decimal("0.00"),
        currency: str = "USD",
    ) -> None:
        if initial_balance < Decimal("0"):
            raise InvalidAmountError("Initial balance cannot be negative.")
        self._raise(AccountOpened(
            account_id=self.account_id,
            owner_name=owner_name,
            initial_balance=initial_balance,
            currency=currency,
        ))

    def deposit(self, amount: Decimal, description: str = "") -> None:
        self._assert_active()
        if amount <= Decimal("0"):
            raise InvalidAmountError("Deposit amount must be positive.")
        self._raise(MoneyDeposited(
            account_id=self.account_id,
            amount=amount,
            description=description,
        ))

    def withdraw(self, amount: Decimal, description: str = "") -> None:
        self._assert_active()
        if amount <= Decimal("0"):
            raise InvalidAmountError("Withdrawal amount must be positive.")
        if amount > self.balance:
            raise InsufficientFundsError(
                f"Cannot withdraw {amount}; balance is {self.balance}."
            )
        self._raise(MoneyWithdrawn(
            account_id=self.account_id,
            amount=amount,
            description=description,
        ))

    def close(self, reason: str = "") -> None:
        self._assert_active()
        self._raise(AccountClosed(account_id=self.account_id, reason=reason))

    # ── Internal event machinery ──────────────────────────────────────────────

    def _raise(self, event: DomainEvent) -> None:
        """Apply event to state AND queue it for persistence."""
        self._apply(event)
        self.version += 1
        self._pending_events.append(event)

    def _apply_saved(self, event: DomainEvent) -> None:
        """Replay a persisted event — updates state only, no queuing."""
        self._apply(event)
        self.version += 1

    def _apply(self, event: DomainEvent) -> None:
        match event:
            case AccountOpened():
                self.owner_name = event.owner_name
                self.balance    = event.initial_balance
                self.currency   = event.currency
                self.status     = "active"
            case MoneyDeposited():
                self.balance   += event.amount
            case MoneyWithdrawn():
                self.balance   -= event.amount
            case AccountClosed():
                self.status     = "closed"

    # ── Snapshot support ──────────────────────────────────────────────────────

    def to_snapshot(self) -> dict:
        return {
            "account_id": str(self.account_id),
            "owner_name": self.owner_name,
            "balance":    str(self.balance),
            "currency":   self.currency,
            "status":     self.status,
            "version":    self.version,
        }

    @classmethod
    def from_snapshot(cls, state: dict) -> "AccountAggregate":
        agg = cls(account_id=UUID(state["account_id"]))
        agg.owner_name = state["owner_name"]
        agg.balance    = Decimal(state["balance"])
        agg.currency   = state["currency"]
        agg.status     = state["status"]
        agg.version    = state["version"]
        return agg

    # ── Guards ────────────────────────────────────────────────────────────────

    def _assert_active(self) -> None:
        if self.status == "new":
            raise AccountNotFoundError(str(self.account_id))
        if self.status == "closed":
            raise AccountAlreadyClosedError(str(self.account_id))

    @property
    def should_snapshot(self) -> bool:
        return (self.version > 0) and (self.version % SNAPSHOT_THRESHOLD == 0)

    def __repr__(self) -> str:
        return (
            f"AccountAggregate(id={self.account_id}, "
            f"balance={self.balance}, version={self.version})"
        )