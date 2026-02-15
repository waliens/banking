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

    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

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

    yield


app = FastAPI(title="Banking V2 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import auth, accounts, categories, transactions, currencies, wallets, imports  # noqa: E402

app.include_router(auth.router, prefix="/api/v2/auth", tags=["auth"])
app.include_router(accounts.router, prefix="/api/v2/accounts", tags=["accounts"])
app.include_router(categories.router, prefix="/api/v2/categories", tags=["categories"])
app.include_router(transactions.router, prefix="/api/v2/transactions", tags=["transactions"])
app.include_router(currencies.router, prefix="/api/v2/currencies", tags=["currencies"])
app.include_router(wallets.router, prefix="/api/v2/wallets", tags=["wallets"])
app.include_router(imports.router, prefix="/api/v2/imports", tags=["imports"])


@app.get("/api/v2/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
