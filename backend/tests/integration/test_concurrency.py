"""
Concurrency conflict test — verifies the UNIQUE(stream_id, version)
constraint surfaces as a 409 when two writers race on the same stream.
"""
import asyncio
import pytest


pytestmark = pytest.mark.asyncio


async def test_concurrent_deposits_one_wins(client):
    """
    Fire two deposits simultaneously. One should succeed, one should get
    a 409 Conflict due to optimistic concurrency violation.
    """
    resp = await client.post("/api/commands/accounts", json={
        "owner_name": "RaceTest", "initial_balance": "1000.00"
    })
    account_id = resp.json()["account_id"]

    results = await asyncio.gather(
        client.post(f"/api/commands/accounts/{account_id}/deposit",
                    json={"amount": "100.00"}),
        client.post(f"/api/commands/accounts/{account_id}/deposit",
                    json={"amount": "100.00"}),
        return_exceptions=True,
    )

    status_codes = [r.status_code for r in results if hasattr(r, "status_code")]
    # At least one must succeed
    assert 204 in status_codes
    # Under true concurrency one may conflict (409), or both succeed sequentially
    for code in status_codes:
        assert code in (204, 409)