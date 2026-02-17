"""Shared test fixtures. Uses SQLite in-memory for fast, isolated tests."""

import datetime
import os
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
    Currency,
    Transaction,
    TransactionGroup,
    User,
    Wallet,
    WalletAccount,
)


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
