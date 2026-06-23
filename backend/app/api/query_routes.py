from uuid import UUID
from fastapi import APIRouter, HTTPException, Query

from app.dependencies import SessionDep
from app.domain.exceptions import AccountNotFoundError
from app.queries.account_queries import (
    get_all_accounts,
    get_balance,
    get_event_stream,
    get_transactions,
)

router = APIRouter(prefix="/queries", tags=["queries"])


@router.get("/accounts")
async def list_accounts(session: SessionDep):
    return await get_all_accounts(session)


@router.get("/accounts/{account_id}/balance")
async def balance(account_id: UUID, session: SessionDep):
    try:
        return await get_balance(account_id, session)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/accounts/{account_id}/transactions")
async def transactions(
    account_id: UUID,
    session: SessionDep,
    limit:  int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        await get_balance(account_id, session)  # existence check
        return await get_transactions(account_id, session, limit=limit, offset=offset)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/accounts/{account_id}/events")
async def event_stream(account_id: UUID, session: SessionDep):
    """Raw event log for the debug/demo view."""
    try:
        await get_balance(account_id, session)
        return await get_event_stream(account_id, session)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))