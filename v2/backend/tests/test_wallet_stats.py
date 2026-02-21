"""Tests for wallet stats endpoints."""

import datetime
from decimal import Decimal

import pytest

from app.models import Account, Category, Currency, Transaction, Wallet, WalletAccount


@pytest.fixture
def wallet_with_accounts(db, account_checking, account_savings):
    """Creates a wallet containing checking and savings accounts."""
    w = Wallet(name="Personal")
    db.add(w)
    db.flush()
    db.add(WalletAccount(id_wallet=w.id, id_account=account_checking.id))
    db.add(WalletAccount(id_wallet=w.id, id_account=account_savings.id))
    db.flush()
    return w


@pytest.fixture
def external_account(db, currency_eur):
    """An account outside the wallet (e.g. a shop)."""
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


class TestWalletBalance:
    def test_balance_initial_only(self, client, auth_headers, wallet_with_accounts):
        r = client.get(f"/api/v2/wallets/{wallet_with_accounts.id}/stats/balance", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data["accounts"]) == 2
        balances = {a["name"]: a["balance"] for a in data["accounts"]}
        assert Decimal(str(balances["Checking"])) == Decimal("1000.00")
        assert Decimal(str(balances["Savings"])) == Decimal("5000.00")

    def test_balance_with_transactions(
        self, client, auth_headers, db, wallet_with_accounts, account_checking, external_account, currency_eur
    ):
        # Expense: checking -> external (100)
        db.add(
            Transaction(
                external_id="exp-1",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 3, 1),
                amount=Decimal("100.00"),
                id_currency=currency_eur.id,
                description="Expense",
            )
        )
        # Income: external -> checking (250)
        db.add(
            Transaction(
                external_id="inc-1",
                id_source=external_account.id,
                id_dest=account_checking.id,
                date=datetime.date(2024, 3, 15),
                amount=Decimal("250.00"),
                id_currency=currency_eur.id,
                description="Income",
            )
        )
        db.flush()

        r = client.get(f"/api/v2/wallets/{wallet_with_accounts.id}/stats/balance", headers=auth_headers)
        assert r.status_code == 200
        balances = {a["name"]: Decimal(str(a["balance"])) for a in r.json()["accounts"]}
        # Checking: 1000 + 250 - 100 = 1150
        assert balances["Checking"] == Decimal("1150.00")
        # Savings: unchanged
        assert balances["Savings"] == Decimal("5000.00")

    def test_balance_excludes_duplicates(
        self, client, auth_headers, db, wallet_with_accounts, account_checking, external_account, currency_eur
    ):
        t1 = Transaction(
            external_id="dup-parent",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 1),
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            description="Original",
        )
        db.add(t1)
        db.flush()

        t2 = Transaction(
            external_id="dup-child",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 1),
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            description="Duplicate",
            id_duplicate_of=t1.id,
        )
        db.add(t2)
        db.flush()

        r = client.get(f"/api/v2/wallets/{wallet_with_accounts.id}/stats/balance", headers=auth_headers)
        balances = {a["name"]: Decimal(str(a["balance"])) for a in r.json()["accounts"]}
        # Only the parent counts: 1000 - 50 = 950
        assert balances["Checking"] == Decimal("950.00")

    def test_balance_wallet_not_found(self, client, auth_headers):
        r = client.get("/api/v2/wallets/99999/stats/balance", headers=auth_headers)
        assert r.status_code == 404


class TestIncomeExpense:
    def test_monthly_aggregation(
        self, client, auth_headers, db, wallet_with_accounts, account_checking, external_account, currency_eur
    ):
        # Expense in March
        db.add(
            Transaction(
                external_id="ie-exp-1",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 3, 10),
                amount=Decimal("80.00"),
                id_currency=currency_eur.id,
                description="March expense",
            )
        )
        # Income in March
        db.add(
            Transaction(
                external_id="ie-inc-1",
                id_source=external_account.id,
                id_dest=account_checking.id,
                date=datetime.date(2024, 3, 20),
                amount=Decimal("200.00"),
                id_currency=currency_eur.id,
                description="March income",
            )
        )
        # Expense in April
        db.add(
            Transaction(
                external_id="ie-exp-2",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 4, 5),
                amount=Decimal("30.00"),
                id_currency=currency_eur.id,
                description="April expense",
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
        assert len(items) == 2

        march = next(i for i in items if i["month"] == 3)
        assert Decimal(str(march["income"])) == Decimal("200.00")
        assert Decimal(str(march["expense"])) == Decimal("80.00")

        april = next(i for i in items if i["month"] == 4)
        assert Decimal(str(april["income"])) == Decimal("0")
        assert Decimal(str(april["expense"])) == Decimal("30.00")

    def test_internal_transfers_excluded(
        self, client, auth_headers, db, wallet_with_accounts, account_checking, account_savings, currency_eur
    ):
        # Internal transfer: checking -> savings (both in wallet)
        db.add(
            Transaction(
                external_id="internal-1",
                id_source=account_checking.id,
                id_dest=account_savings.id,
                date=datetime.date(2024, 5, 1),
                amount=Decimal("500.00"),
                id_currency=currency_eur.id,
                description="Internal transfer",
            )
        )
        db.flush()

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/income-expense",
            params={"year": 2024},
            headers=auth_headers,
        )
        assert r.status_code == 200
        # Internal transfers should not appear
        assert r.json()["items"] == []

    def test_wallet_not_found(self, client, auth_headers):
        r = client.get("/api/v2/wallets/99999/stats/income-expense", headers=auth_headers)
        assert r.status_code == 404


class TestPerCategory:
    def test_groups_by_category(
        self,
        client,
        auth_headers,
        db,
        wallet_with_accounts,
        account_checking,
        external_account,
        currency_eur,
        category_food,
        category_salary,
    ):
        # Expense: food
        db.add(
            Transaction(
                external_id="cat-1",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 3, 1),
                amount=Decimal("45.00"),
                id_currency=currency_eur.id,
                id_category=category_food.id,
                description="Groceries",
            )
        )
        db.add(
            Transaction(
                external_id="cat-2",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 3, 5),
                amount=Decimal("30.00"),
                id_currency=currency_eur.id,
                id_category=category_food.id,
                description="Restaurant",
            )
        )
        # Uncategorized expense
        db.add(
            Transaction(
                external_id="cat-3",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 3, 10),
                amount=Decimal("20.00"),
                id_currency=currency_eur.id,
                description="Unknown",
            )
        )
        db.flush()

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 2  # Food and uncategorized

        food_item = next(i for i in items if i["category_name"] == "Food")
        assert Decimal(str(food_item["amount"])) == Decimal("75.00")
        assert food_item["category_color"] == "#FF0000"

        uncat_item = next(i for i in items if i["id_category"] is None)
        assert Decimal(str(uncat_item["amount"])) == Decimal("20.00")

    def test_income_only_filter(
        self,
        client,
        auth_headers,
        db,
        wallet_with_accounts,
        account_checking,
        external_account,
        currency_eur,
        category_salary,
    ):
        # Income with salary category
        db.add(
            Transaction(
                external_id="inc-cat-1",
                id_source=external_account.id,
                id_dest=account_checking.id,
                date=datetime.date(2024, 3, 1),
                amount=Decimal("3000.00"),
                id_currency=currency_eur.id,
                id_category=category_salary.id,
                description="Salary",
            )
        )
        # Expense (should not appear with income_only)
        db.add(
            Transaction(
                external_id="exp-cat-1",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 3, 5),
                amount=Decimal("50.00"),
                id_currency=currency_eur.id,
                description="Expense",
            )
        )
        db.flush()

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            params={"income_only": True},
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["category_name"] == "Salary"
        assert Decimal(str(items[0]["amount"])) == Decimal("3000.00")

    def test_date_range_filter(
        self,
        client,
        auth_headers,
        db,
        wallet_with_accounts,
        account_checking,
        external_account,
        currency_eur,
    ):
        db.add(
            Transaction(
                external_id="dr-1",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 1, 15),
                amount=Decimal("100.00"),
                id_currency=currency_eur.id,
                description="January",
            )
        )
        db.add(
            Transaction(
                external_id="dr-2",
                id_source=account_checking.id,
                id_dest=external_account.id,
                date=datetime.date(2024, 6, 15),
                amount=Decimal("200.00"),
                id_currency=currency_eur.id,
                description="June",
            )
        )
        db.flush()

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            params={"date_from": "2024-03-01", "date_to": "2024-12-31"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert Decimal(str(items[0]["amount"])) == Decimal("200.00")

    def test_wallet_not_found(self, client, auth_headers):
        r = client.get("/api/v2/wallets/99999/stats/per-category", headers=auth_headers)
        assert r.status_code == 404
