from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from decimal import Decimal

from app.commands.account_commands import (
    handle_close_account,
    handle_deposit,
    handle_open_account,
    handle_withdraw,
)
from app.dependencies import BusDep, SessionDep
from app.domain.commands import (
    CloseAccountCommand,
    DepositMoneyCommand,
    OpenAccountCommand,
    WithdrawMoneyCommand,
)
from app.domain.exceptions import (
    AccountAlreadyClosedError,
    AccountNotFoundError,
    ConcurrencyConflictError,
    InsufficientFundsError,
    InvalidAmountError,
)

router = APIRouter(prefix="/commands", tags=["commands"])


# ── Request / response schemas ────────────────────────────────────────────────

class OpenAccountRequest(BaseModel):
    owner_name:      str
    initial_balance: Decimal = Decimal("0.00")
    currency:        str     = "USD"

class OpenAccountResponse(BaseModel):
    account_id: UUID

class MoneyRequest(BaseModel):
    amount:      Decimal
    description: str = ""

class CloseRequest(BaseModel):
    reason: str = ""


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/accounts", response_model=OpenAccountResponse, status_code=201)
async def open_account(body: OpenAccountRequest, session: SessionDep, bus: BusDep):
    try:
        account_id = await handle_open_account(
            OpenAccountCommand(**body.model_dump()), session, bus
        )
        return OpenAccountResponse(account_id=account_id)
    except InvalidAmountError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/accounts/{account_id}/deposit", status_code=204)
async def deposit(account_id: UUID, body: MoneyRequest, session: SessionDep, bus: BusDep):
    try:
        await handle_deposit(
            DepositMoneyCommand(account_id=account_id, **body.model_dump()),
            session, bus,
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (InvalidAmountError, AccountAlreadyClosedError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConcurrencyConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/accounts/{account_id}/withdraw", status_code=204)
async def withdraw(account_id: UUID, body: MoneyRequest, session: SessionDep, bus: BusDep):
    try:
        await handle_withdraw(
            WithdrawMoneyCommand(account_id=account_id, **body.model_dump()),
            session, bus,
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except (InvalidAmountError, AccountAlreadyClosedError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConcurrencyConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/accounts/{account_id}/close", status_code=204)
async def close_account(account_id: UUID, body: CloseRequest, session: SessionDep, bus: BusDep):
    try:
        await handle_close_account(
            CloseAccountCommand(account_id=account_id, **body.model_dump()),
            session, bus,
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AccountAlreadyClosedError as e:
        raise HTTPException(status_code=422, detail=str(e))