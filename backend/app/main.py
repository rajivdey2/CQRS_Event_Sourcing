from contextlib import asynccontextmanager
import logging
import asyncio
import os
import re

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.infrastructure.database import AsyncSessionLocal, engine
from app.infrastructure.event_bus import event_bus
from app.projectors.balance_projector import BalanceProjector
from app.projectors.transaction_projector import TransactionProjector
from app.api import command_routes, query_routes, admin_routes
from app.domain.exceptions import (
    AccountAlreadyClosedError,
    AccountNotFoundError,
    ConcurrencyConflictError,
    InsufficientFundsError,
    InvalidAmountError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


async def _wait_for_db(
    retries: int = int(os.getenv("DB_RETRIES", "20")),
    delay: float = float(os.getenv("DB_RETRY_DELAY", "5")),
) -> None:
    logger.info("Connecting to DB (up to %d attempts)…", retries)
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database reachable on attempt %d", attempt)
            return
        except Exception as e:
            logger.warning("DB not ready (attempt %d/%d): %s", attempt, retries, e)
            if attempt == retries:
                raise RuntimeError("Database never became reachable") from e
            await asyncio.sleep(delay)


def _split_sql(ddl: str) -> list[str]:
    """
    Split a multi-statement SQL file into individual statements.
    asyncpg cannot execute multiple statements in one prepared call.
    Strips comments and blank statements.
    """
    # Remove single-line comments
    ddl = re.sub(r'--[^\n]*', '', ddl)
    # Split on semicolons
    statements = [s.strip() for s in ddl.split(';')]
    # Filter out empty strings
    return [s for s in statements if s]


async def _init_schema() -> None:
    sql_path = os.path.join(os.path.dirname(__file__), "..", "init.sql")
    if not os.path.exists(sql_path):
        logger.warning("init.sql not found — skipping schema init")
        return

    with open(sql_path) as f:
        ddl = f.read()

    statements = _split_sql(ddl)
    logger.info("Running %d schema statements…", len(statements))

    async with engine.begin() as conn:
        for stmt in statements:
            await conn.execute(text(stmt))

    logger.info("Schema initialised")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _wait_for_db()
    await _init_schema()

    balance_proj     = BalanceProjector(AsyncSessionLocal)
    transaction_proj = TransactionProjector(AsyncSessionLocal)

    for event_type in ("AccountOpened", "MoneyDeposited", "MoneyWithdrawn", "AccountClosed"):
        event_bus.subscribe(event_type, balance_proj)
    for event_type in ("AccountOpened", "MoneyDeposited", "MoneyWithdrawn"):
        event_bus.subscribe(event_type, transaction_proj)

    logger.info("Event bus wired — projectors registered")
    yield
    logger.info("Shutting down")
    await engine.dispose()


app = FastAPI(
    title="CQRS Ledger API",
    description="Bank account ledger — CQRS + Event Sourcing",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(command_routes.router, prefix="/api")
app.include_router(query_routes.router,  prefix="/api")
app.include_router(admin_routes.router,  prefix="/api")


@app.exception_handler(AccountNotFoundError)
async def not_found(_: Request, exc: AccountNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(InsufficientFundsError)
async def insufficient_funds(_: Request, exc: InsufficientFundsError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(InvalidAmountError)
async def invalid_amount(_: Request, exc: InvalidAmountError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(AccountAlreadyClosedError)
async def already_closed(_: Request, exc: AccountAlreadyClosedError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(ConcurrencyConflictError)
async def concurrency_conflict(_: Request, exc: ConcurrencyConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok"}

@app.get("/", tags=["ops"])
async def root():
    return {"app": "CQRS Ledger", "docs": "/docs", "version": "1.0.0"}