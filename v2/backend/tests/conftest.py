"""Shared test fixtures. Uses SQLite in-memory for fast, isolated tests."""

import datetime
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from decimal import Decimal

os.environ.setdefault("BANKING_COOKIE_SECURE", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token
from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.models import (
    Account,
    AccountAlias,
    Category,
    CategorySplit,
    Currency,
    ImportRecord,
    Transaction,
    TransactionGroup,
    User,
    Wallet,
    WalletAccount,
)


# Replace the production lifespan (which runs Alembic migrations and seeds
# data against the real PostgreSQL engine) with a no-op so tests can run
# against an in-memory SQLite database without a running PostgreSQL server.
@asynccontextmanager
async def _test_lifespan(app) -> AsyncIterator[None]:
    yield

app.router.lifespan_context = _test_lifespan


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # enable foreign keys in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(test_engine) -> Session:
    """Provides a clean database session per test — rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, autoflush=False, expire_on_commit=False)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db) -> TestClient:
    """TestClient with dependency override for the DB session."""

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---- Data factories ----


@pytest.fixture
def currency_eur(db) -> Currency:
    c = Currency(id=1, symbol="€", short_name="EUR", long_name="Euro")
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def user(db) -> User:
    u = User(username="testuser", password_hash=User.hash_password("testpass123"))
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def auth_headers(user) -> dict:
    """Authorization headers with a valid access token for `user`."""
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def account_checking(db, currency_eur) -> Account:
    a = Account(
        name="Checking",
        number="BE1234",
        initial_balance=Decimal("1000.00"),
        id_currency=currency_eur.id,
        institution="belfius",
        is_active=True,
    )
    db.add(a)
    db.flush()
    return a


@pytest.fixture
def account_savings(db, currency_eur) -> Account:
    a = Account(
        name="Savings",
        number="BE5678",
        initial_balance=Decimal("5000.00"),
        id_currency=currency_eur.id,
        institution="belfius",
        is_active=True,
    )
    db.add(a)
    db.flush()
    return a


@pytest.fixture
def category_food(db) -> Category:
    c = Category(name="Food", color="#FF0000", sort_order=0, is_income=False)
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def category_salary(db) -> Category:
    c = Category(name="Salary", color="#00FF00", sort_order=1, is_income=True)
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def category_child(db, category_food) -> Category:
    c = Category(name="Groceries", color="#FF5555", id_parent=category_food.id, sort_order=0, is_income=False)
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def sample_transaction(db, account_checking, account_savings, currency_eur) -> Transaction:
    t = Transaction(
        external_id="test-tx-001",
        id_source=account_checking.id,
        id_dest=account_savings.id,
        date=datetime.date(2024, 6, 15),
        amount=Decimal("50.00"),
        id_currency=currency_eur.id,
        data_source="manual",
        description="Test transfer",
        is_reviewed=False,
    )
    db.add(t)
    db.flush()
    return t


@pytest.fixture
def wallet(db, account_checking) -> Wallet:
    w = Wallet(name="Main Wallet", description="Test wallet")
    db.add(w)
    db.flush()
    wa = WalletAccount(id_wallet=w.id, id_account=account_checking.id, contribution_ratio=1.0)
    db.add(wa)
    db.flush()
    return w


def categorize(db: Session, transaction: Transaction, category: Category) -> CategorySplit:
    """Helper to create a category split for a transaction (simulates single-category assignment)."""
    effective = transaction.effective_amount if transaction.effective_amount is not None else transaction.amount
    cs = CategorySplit(id_transaction=transaction.id, id_category=category.id, amount=effective)
    db.add(cs)
    db.flush()
    return cs


@pytest.fixture
def import_record(db, account_checking, account_savings, currency_eur) -> ImportRecord:
    ir = ImportRecord(
        format="belfius",
        filenames=["test.csv"],
        total_transactions=3,
        new_transactions=2,
        duplicate_transactions=1,
        skipped_transactions=0,
        new_accounts=0,
        auto_tagged=0,
        date_earliest=datetime.date(2024, 6, 1),
        date_latest=datetime.date(2024, 6, 30),
    )
    db.add(ir)
    db.flush()
    # Create linked transactions
    for i in range(2):
        t = Transaction(
            external_id=f"import-tx-{i}",
            id_source=account_checking.id,
            id_dest=account_savings.id,
            date=datetime.date(2024, 6, 15),
            amount=Decimal("25.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
            description=f"Import test {i}",
            is_reviewed=False,
            id_import=ir.id,
        )
        db.add(t)
    db.flush()
    return ir
