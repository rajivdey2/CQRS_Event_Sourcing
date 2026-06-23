from contextlib import asynccontextmanager
import logging
import asyncio

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


async def _wait_for_db(retries: int = 10, delay: float = 3.0) -> None:
    """
    Render starts the web service before the managed Postgres is fully ready.
    Retry the connection with backoff so startup doesn't fail on a race.
    """
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


async def _init_schema() -> None:
    """
    Run init.sql on startup — idempotent (IF NOT EXISTS throughout).
    Safe to run on every cold start; Render free tier spins down regularly.
    """
    import os
    sql_path = os.path.join(os.path.dirname(__file__), "..", "init.sql")
    if not os.path.exists(sql_path):
        logger.warning("init.sql not found at %s — skipping schema init", sql_path)
        return
    with open(sql_path) as f:
        ddl = f.read()
    async with engine.begin() as conn:
        await conn.execute(text(ddl))
    logger.info("Schema initialised")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("Connecting to database: %s", settings.async_database_url[:40] + "…")
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
    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Shutting down")
    await engine.dispose()


app = FastAPI(
    title="CQRS Ledger API",
    description="Bank account ledger — CQRS + Event Sourcing",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(command_routes.router, prefix="/api")
app.include_router(query_routes.router,  prefix="/api")
app.include_router(admin_routes.router,  prefix="/api")


# ── Global exception handlers ─────────────────────────────────────────────────
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


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok"}

@app.get("/", tags=["ops"])
async def root():
    return {"app": "CQRS Ledger", "docs": "/docs", "version": "1.0.0"}