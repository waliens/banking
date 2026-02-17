import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    import app.models as _models  # noqa: F401 — ensure all models are registered
    from app.database import SessionLocal
    from app.models.currency import Currency
    from app.models.user import User

    logger.info("Running database migrations...")
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect, text

    # Bootstrap: create tables that don't exist yet (handles fresh databases)
    Base.metadata.create_all(bind=engine)

    # Transition from create_all-only to Alembic: if alembic_version table
    # doesn't exist or has no rows, stamp the baseline so upgrade proceeds
    # from the right point.
    inspector = inspect(engine)
    if "alembic_version" not in inspector.get_table_names():
        logger.info("No alembic_version table — stamping baseline")
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "0001")
    else:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT version_num FROM alembic_version")).first()
            if row is None:
                logger.info("Empty alembic_version — stamping baseline")
                alembic_cfg = Config("alembic.ini")
                command.stamp(alembic_cfg, "0001")

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    db = SessionLocal()
    try:
        if db.query(Currency).count() == 0:
            logger.info("No currencies found — seeding defaults")
            db.add_all(
                [
                    Currency(symbol="€", short_name="EUR", long_name="Euro"),
                    Currency(symbol="$", short_name="USD", long_name="US Dollar"),
                    Currency(symbol="£", short_name="GBP", long_name="British Pound"),
                ]
            )
            db.commit()

        if db.query(User).count() == 0:
            logger.info("No users found — creating default admin account")
            db.add(User(username="admin", password_hash=User.hash_password("password")))
            db.commit()
    finally:
        db.close()

    from app.tasks.scheduler import init_scheduler

    init_scheduler()

    yield

    from app.tasks.scheduler import shutdown_scheduler

    shutdown_scheduler()


app = FastAPI(title="Banking V2 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import (
    auth,
    accounts,
    categories,
    transactions,
    transaction_groups,
    currencies,
    wallets,
    wallet_stats,
    imports,
    ml,
    tag_rules,
)  # noqa: E402

app.include_router(auth.router, prefix="/api/v2/auth", tags=["auth"])
app.include_router(accounts.router, prefix="/api/v2/accounts", tags=["accounts"])
app.include_router(categories.router, prefix="/api/v2/categories", tags=["categories"])
app.include_router(transactions.router, prefix="/api/v2/transactions", tags=["transactions"])
app.include_router(transaction_groups.router, prefix="/api/v2/transaction-groups", tags=["transaction-groups"])
app.include_router(currencies.router, prefix="/api/v2/currencies", tags=["currencies"])
app.include_router(wallets.router, prefix="/api/v2/wallets", tags=["wallets"])
app.include_router(wallet_stats.router, prefix="/api/v2/wallets", tags=["wallet-stats"])
app.include_router(imports.router, prefix="/api/v2/imports", tags=["imports"])
app.include_router(ml.router, prefix="/api/v2/ml", tags=["ml"])
app.include_router(tag_rules.router, prefix="/api/v2/tag-rules", tags=["tag-rules"])


@app.get("/api/v2/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
