from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # startup
    yield
    # shutdown


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
