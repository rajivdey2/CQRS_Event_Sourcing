"""
Integration tests: spin up the full FastAPI app against a test DB and
exercise complete command → event store → projector → query roundtrips.

Run with:
    pytest tests/integration/ -v
"""
import pytest
from decimal import Decimal


pytestmark = pytest.mark.asyncio


class TestAccountLifecycle:
    async def test_open_account_returns_201_with_id(self, client):
        resp = await client.post("/api/commands/accounts", json={
            "owner_name": "Alice",
            "initial_balance": "500.00",
            "currency": "USD",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "account_id" in data

    async def test_balance_readable_after_open(self, client):
        resp = await client.post("/api/commands/accounts", json={
            "owner_name": "Bob",
            "initial_balance": "200.00",
        })
        account_id = resp.json()["account_id"]

        bal = await client.get(f"/api/queries/accounts/{account_id}/balance")
        assert bal.status_code == 200
        assert Decimal(bal.json()["balance"]) == Decimal("200.00")

    async def test_deposit_increases_balance(self, client):
        resp = await client.post("/api/commands/accounts", json={
            "owner_name": "Carol", "initial_balance": "100.00"
        })
        account_id = resp.json()["account_id"]

        await client.post(f"/api/commands/accounts/{account_id}/deposit",
                          json={"amount": "75.00", "description": "bonus"})

        bal = await client.get(f"/api/queries/accounts/{account_id}/balance")
        assert Decimal(bal.json()["balance"]) == Decimal("175.00")

    async def test_withdraw_decreases_balance(self, client):
        resp = await client.post("/api/commands/accounts", json={
            "owner_name": "Dan", "initial_balance": "300.00"
        })
        account_id = resp.json()["account_id"]

        await client.post(f"/api/commands/accounts/{account_id}/withdraw",
                          json={"amount": "120.00"})

        bal = await client.get(f"/api/queries/accounts/{account_id}/balance")
        assert Decimal(bal.json()["balance"]) == Decimal("180.00")

    async def test_overdraft_returns_422(self, client):
        resp = await client.post("/api/commands/accounts", json={
            "owner_name": "Eve", "initial_balance": "50.00"
        })
        account_id = resp.json()["account_id"]

        resp = await client.post(f"/api/commands/accounts/{account_id}/withdraw",
                                 json={"amount": "999.00"})
        assert resp.status_code == 422
        assert "balance" in resp.json()["detail"].lower()

    async def test_transactions_appear_in_history(self, client):
        resp = await client.post("/api/commands/accounts", json={
            "owner_name": "Frank", "initial_balance": "0.00"
        })
        account_id = resp.json()["account_id"]

        await client.post(f"/api/commands/accounts/{account_id}/deposit",
                          json={"amount": "100.00", "description": "pay"})
        await client.post(f"/api/commands/accounts/{account_id}/deposit",
                          json={"amount": "50.00", "description": "gift"})
        await client.post(f"/api/commands/accounts/{account_id}/withdraw",
                          json={"amount": "30.00", "description": "coffee"})

        txns = await client.get(f"/api/queries/accounts/{account_id}/transactions")
        assert txns.status_code == 200
        assert len(txns.json()) == 3

    async def test_close_account_prevents_further_ops(self, client):
        resp = await client.post("/api/commands/accounts", json={
            "owner_name": "Grace", "initial_balance": "100.00"
        })
        account_id = resp.json()["account_id"]

        await client.post(f"/api/commands/accounts/{account_id}/close",
                          json={"reason": "test"})

        resp = await client.post(f"/api/commands/accounts/{account_id}/deposit",
                                 json={"amount": "10.00"})
        assert resp.status_code == 422

    async def test_unknown_account_returns_404(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/queries/accounts/{fake_id}/balance")
        assert resp.status_code == 404

    async def test_event_stream_records_all_events(self, client):
        resp = await client.post("/api/commands/accounts", json={
            "owner_name": "Hank", "initial_balance": "0.00"
        })
        account_id = resp.json()["account_id"]

        await client.post(f"/api/commands/accounts/{account_id}/deposit",
                          json={"amount": "200.00"})

        events = await client.get(f"/api/queries/accounts/{account_id}/events")
        assert events.status_code == 200
        types = [e["event_type"] for e in events.json()]
        assert "AccountOpened"  in types
        assert "MoneyDeposited" in types

    async def test_rebuild_projection_endpoint(self, client):
        # seed some data first
        resp = await client.post("/api/commands/accounts", json={
            "owner_name": "Ivy", "initial_balance": "100.00"
        })
        account_id = resp.json()["account_id"]
        await client.post(f"/api/commands/accounts/{account_id}/deposit",
                          json={"amount": "50.00"})

        rebuild = await client.post("/api/admin/rebuild-projection")
        assert rebuild.status_code == 200
        assert rebuild.json()["replayed"] >= 2

        # balance must be intact after rebuild
        bal = await client.get(f"/api/queries/accounts/{account_id}/balance")
        assert Decimal(bal.json()["balance"]) == Decimal("150.00")

    async def test_stats_endpoint(self, client):
        resp = await client.get("/api/admin/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert "total_events" in body
        assert "total_accounts" in body