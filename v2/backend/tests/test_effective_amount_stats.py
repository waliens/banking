"""Tests that wallet stats use effective_amount when set."""

import datetime
from decimal import Decimal

import pytest

from app.models import Account, Category, CategorySplit, Currency, Transaction, Wallet, WalletAccount
from tests.conftest import categorize


@pytest.fixture
def wallet_with_accounts(db, account_checking, account_savings):
    w = Wallet(name="Personal")
    db.add(w)
    db.flush()
    db.add(WalletAccount(id_wallet=w.id, id_account=account_checking.id))
    db.add(WalletAccount(id_wallet=w.id, id_account=account_savings.id))
    db.flush()
    return w


@pytest.fixture
def external_account(db, currency_eur):
    a = Account(
        name="Shop",
        number="EXT001",
        initial_balance=Decimal("0"),
        id_currency=currency_eur.id,
        institution="other",
        is_active=True,
    )
    db.add(a)
    db.flush()
    return a


class TestBalanceUsesEffectiveAmount:
    def test_balance_uses_effective_amount(
        self, client, auth_headers, db, wallet_with_accounts, account_checking, external_account, currency_eur
    ):
        """Transaction with effective_amount → balance uses effective."""
        db.add(
            Transaction(
                external_id="eff-1",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 3, 1),
                amount=Decimal("100.00"),
                effective_amount=Decimal("25.00"),
                id_currency=currency_eur.id,
                description="Group expense",
            )
        )
        db.flush()

        r = client.get(f"/api/v2/wallets/{wallet_with_accounts.id}/stats/balance", headers=auth_headers)
        assert r.status_code == 200
        balances = {a["name"]: Decimal(str(a["balance"])) for a in r.json()["accounts"]}
        # Checking: 1000 - 25 (effective) = 975
        assert balances["Checking"] == Decimal("975.00")

    def test_balance_null_effective_uses_amount(
        self, client, auth_headers, db, wallet_with_accounts, account_checking, external_account, currency_eur
    ):
        """Transaction without effective_amount → balance uses raw amount."""
        db.add(
            Transaction(
                external_id="eff-2",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 3, 1),
                amount=Decimal("100.00"),
                id_currency=currency_eur.id,
                description="Normal expense",
            )
        )
        db.flush()

        r = client.get(f"/api/v2/wallets/{wallet_with_accounts.id}/stats/balance", headers=auth_headers)
        balances = {a["name"]: Decimal(str(a["balance"])) for a in r.json()["accounts"]}
        # Checking: 1000 - 100 = 900
        assert balances["Checking"] == Decimal("900.00")


class TestIncomeExpenseUsesEffectiveAmount:
    def test_income_expense_uses_effective_amount(
        self, client, auth_headers, db, wallet_with_accounts, account_checking, external_account, currency_eur
    ):
        # Outgoing with effective_amount
        db.add(
            Transaction(
                external_id="ie-eff-1",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 3, 10),
                amount=Decimal("100.00"),
                effective_amount=Decimal("25.00"),
                id_currency=currency_eur.id,
                description="Group expense",
            )
        )
        # Incoming reimbursement with effective_amount=0
        db.add(
            Transaction(
                external_id="ie-eff-2",
                id_source=external_account.id,
                id_dest=account_checking.id,
                date=datetime.date(2024, 3, 15),
                amount=Decimal("75.00"),
                effective_amount=Decimal("0"),
                id_currency=currency_eur.id,
                description="Reimbursement",
            )
        )
        db.flush()

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/income-expense",
            params={"year": 2024},
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        march = items[0]
        assert Decimal(str(march["expense"])) == Decimal("25.00")
        assert Decimal(str(march["income"])) == Decimal("0")


class TestPerCategoryUsesEffectiveAmount:
    def test_per_category_uses_effective_amount(
        self, client, auth_headers, db, wallet_with_accounts, account_checking, external_account, currency_eur, category_food
    ):
        t = Transaction(
            external_id="cat-eff-1",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 1),
            amount=Decimal("100.00"),
            effective_amount=Decimal("25.00"),
            id_currency=currency_eur.id,
            description="Group dinner",
        )
        db.add(t)
        db.flush()
        categorize(db, t, category_food)

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert Decimal(str(items[0]["amount"])) == Decimal("25.00")
