import pytest
from decimal import Decimal
from uuid import uuid4

from app.domain.aggregate import AccountAggregate
from app.domain.events import AccountOpened, MoneyDeposited, MoneyWithdrawn, AccountClosed
from app.domain.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    AccountAlreadyClosedError,
    AccountNotFoundError,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def opened_account(balance: str = "100.00") -> AccountAggregate:
    agg = AccountAggregate()
    agg.open(owner_name="Alice", initial_balance=Decimal(balance))
    agg._pending_events.clear()   # simulate persisted state
    agg.version = 1
    return agg


# ── open ──────────────────────────────────────────────────────────────────────

class TestOpen:
    def test_emits_account_opened_event(self):
        agg = AccountAggregate()
        agg.open(owner_name="Bob", initial_balance=Decimal("50.00"))
        assert len(agg._pending_events) == 1
        assert isinstance(agg._pending_events[0], AccountOpened)

    def test_sets_balance_and_status(self):
        agg = AccountAggregate()
        agg.open(owner_name="Bob", initial_balance=Decimal("200.00"))
        assert agg.balance == Decimal("200.00")
        assert agg.status == "active"

    def test_rejects_negative_initial_balance(self):
        agg = AccountAggregate()
        with pytest.raises(InvalidAmountError):
            agg.open(owner_name="Bob", initial_balance=Decimal("-1.00"))

    def test_zero_initial_balance_is_ok(self):
        agg = AccountAggregate()
        agg.open(owner_name="Bob", initial_balance=Decimal("0.00"))
        assert agg.balance == Decimal("0.00")


# ── deposit ───────────────────────────────────────────────────────────────────

class TestDeposit:
    def test_increases_balance(self):
        agg = opened_account("100.00")
        agg.deposit(Decimal("50.00"))
        assert agg.balance == Decimal("150.00")

    def test_emits_money_deposited(self):
        agg = opened_account()
        agg.deposit(Decimal("10.00"))
        assert isinstance(agg._pending_events[0], MoneyDeposited)

    def test_rejects_zero_amount(self):
        agg = opened_account()
        with pytest.raises(InvalidAmountError):
            agg.deposit(Decimal("0.00"))

    def test_rejects_negative_amount(self):
        agg = opened_account()
        with pytest.raises(InvalidAmountError):
            agg.deposit(Decimal("-5.00"))

    def test_rejected_on_closed_account(self):
        agg = opened_account()
        agg.close()
        agg._pending_events.clear()
        with pytest.raises(AccountAlreadyClosedError):
            agg.deposit(Decimal("10.00"))


# ── withdraw ──────────────────────────────────────────────────────────────────

class TestWithdraw:
    def test_decreases_balance(self):
        agg = opened_account("200.00")
        agg.withdraw(Decimal("80.00"))
        assert agg.balance == Decimal("120.00")

    def test_emits_money_withdrawn(self):
        agg = opened_account("200.00")
        agg.withdraw(Decimal("50.00"))
        assert isinstance(agg._pending_events[0], MoneyWithdrawn)

    def test_raises_insufficient_funds(self):
        agg = opened_account("50.00")
        with pytest.raises(InsufficientFundsError):
            agg.withdraw(Decimal("100.00"))

    def test_exact_balance_withdrawal_succeeds(self):
        agg = opened_account("100.00")
        agg.withdraw(Decimal("100.00"))
        assert agg.balance == Decimal("0.00")

    def test_rejects_zero_amount(self):
        agg = opened_account()
        with pytest.raises(InvalidAmountError):
            agg.withdraw(Decimal("0.00"))


# ── replay / version ──────────────────────────────────────────────────────────

class TestReplay:
    def test_replay_rebuilds_balance(self):
        agg = AccountAggregate(account_id=uuid4())
        events = [
            AccountOpened(account_id=agg.account_id, owner_name="Eve", initial_balance=Decimal("0")),
            MoneyDeposited(account_id=agg.account_id, amount=Decimal("300")),
            MoneyWithdrawn(account_id=agg.account_id, amount=Decimal("100")),
            MoneyDeposited(account_id=agg.account_id, amount=Decimal("50")),
        ]
        for e in events:
            agg._apply_saved(e)
        assert agg.balance == Decimal("250")
        assert agg.version == 4

    def test_version_increments_per_saved_event(self):
        agg = opened_account()
        agg.deposit(Decimal("10"))
        agg._apply_saved(agg._pending_events[0])
        assert agg.version == 2

    def test_snapshot_threshold_flag(self):
        agg = opened_account()
        agg.version = 20
        assert agg.should_snapshot is True
        agg.version = 19
        assert agg.should_snapshot is False


# ── close ─────────────────────────────────────────────────────────────────────

class TestClose:
    def test_emits_account_closed(self):
        agg = opened_account()
        agg.close(reason="Customer request")
        assert isinstance(agg._pending_events[0], AccountClosed)
        assert agg.status == "closed"

    def test_double_close_raises(self):
        agg = opened_account()
        agg.close()
        agg._pending_events.clear()
        with pytest.raises(AccountAlreadyClosedError):
            agg.close()