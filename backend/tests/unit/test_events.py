from decimal import Decimal
from uuid import uuid4

from app.domain.events import (
    AccountOpened,
    MoneyDeposited,
    MoneyWithdrawn,
    AccountClosed,
    EVENT_REGISTRY,
)


class TestEventSerialisation:
    def test_account_opened_to_dict(self):
        account_id = uuid4()
        event = AccountOpened(
            account_id=account_id,
            owner_name="Alice",
            initial_balance=Decimal("100.00"),
            currency="USD",
        )
        d = event.to_dict()
        assert d["account_id"] == str(account_id)
        assert d["owner_name"] == "Alice"
        assert d["initial_balance"] == "100.00"
        assert d["currency"] == "USD"

    def test_money_deposited_to_dict(self):
        event = MoneyDeposited(account_id=uuid4(), amount=Decimal("50.00"), description="salary")
        d = event.to_dict()
        assert d["amount"] == "50.00"
        assert d["description"] == "salary"

    def test_events_are_immutable(self):
        import pytest
        event = MoneyDeposited(account_id=uuid4(), amount=Decimal("10.00"))
        with pytest.raises((AttributeError, TypeError)):
            event.amount = Decimal("999.00")  # type: ignore

    def test_event_registry_contains_all_types(self):
        expected = {"AccountOpened", "MoneyDeposited", "MoneyWithdrawn", "AccountClosed"}
        assert expected == set(EVENT_REGISTRY.keys())

    def test_event_registry_maps_to_correct_class(self):
        assert EVENT_REGISTRY["MoneyDeposited"] is MoneyDeposited
        assert EVENT_REGISTRY["AccountOpened"]  is AccountOpened