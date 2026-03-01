"""Tests for stats consistency with transaction groups.

Business rules:
- A transaction in a group must NOT be counted individually in stats
- A group's accounted value is its net expense (total_paid - total_reimbursed)
- Group category splits determine per-category allocation
- Groups without category splits appear as uncategorized
- Internal-only groups (all transactions between wallet accounts) are excluded
- Duplicates are always excluded
"""

import datetime
from decimal import Decimal

import pytest

from app.models import Account, Category, CategorySplit, Transaction, Wallet, WalletAccount
from tests.conftest import categorize, categorize_group, create_group


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


@pytest.fixture
def wallet_account_ids(account_checking, account_savings):
    return {account_checking.id, account_savings.id}


class TestPerCategoryWithGroups:
    """Per-category stats must account for transaction groups correctly."""

    def test_group_category_splits_appear_in_stats(
        self, client, auth_headers, db, wallet_with_accounts,
        account_checking, external_account, currency_eur, category_food,
        wallet_account_ids,
    ):
        """A group with category splits should appear in per-category stats."""
        # Payment out: €100
        payment = Transaction(
            external_id="grp-pay-1",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 10),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            description="Dinner payment",
        )
        # Reimbursement in: €40
        reimb = Transaction(
            external_id="grp-reimb-1",
            id_source=external_account.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 3, 15),
            amount=Decimal("40.00"),
            id_currency=currency_eur.id,
            description="Friend reimbursement",
        )
        db.add_all([payment, reimb])
        db.flush()

        group = create_group(db, "Dinner", [payment, reimb], wallet_account_ids)
        # Net expense = 100 - 40 = 60
        categorize_group(db, group, category_food, Decimal("60.00"))

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["category_name"] == "Food"
        assert Decimal(str(items[0]["amount"])) == Decimal("60.00")

    def test_grouped_transactions_not_double_counted(
        self, client, auth_headers, db, wallet_with_accounts,
        account_checking, external_account, currency_eur, category_food,
        wallet_account_ids,
    ):
        """Individual transactions in a group must NOT appear separately in stats."""
        # Group: pay €100, get €40 back, net = €60
        payment = Transaction(
            external_id="grp-pay-2",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 10),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            description="Group payment",
        )
        reimb = Transaction(
            external_id="grp-reimb-2",
            id_source=external_account.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 3, 15),
            amount=Decimal("40.00"),
            id_currency=currency_eur.id,
            description="Group reimbursement",
        )
        db.add_all([payment, reimb])
        db.flush()

        group = create_group(db, "Group", [payment, reimb], wallet_account_ids)
        categorize_group(db, group, category_food, Decimal("60.00"))

        # Also add an individual (non-grouped) uncategorized expense
        db.add(Transaction(
            external_id="solo-1",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 20),
            amount=Decimal("30.00"),
            id_currency=currency_eur.id,
            description="Solo expense",
        ))
        db.flush()

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]

        # Should have Food=60 (from group) and uncategorized=30 (individual)
        amounts_by_cat = {i["category_name"]: Decimal(str(i["amount"])) for i in items}
        assert amounts_by_cat["Food"] == Decimal("60.00")
        assert amounts_by_cat.get(None) == Decimal("30.00")  # uncategorized
        assert len(items) == 2

    def test_uncategorized_group_appears_as_uncategorized(
        self, client, auth_headers, db, wallet_with_accounts,
        account_checking, external_account, currency_eur,
        wallet_account_ids,
    ):
        """A group without category splits should appear as uncategorized."""
        payment = Transaction(
            external_id="grp-pay-3",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 10),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            description="Uncategorized group payment",
        )
        reimb = Transaction(
            external_id="grp-reimb-3",
            id_source=external_account.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 3, 15),
            amount=Decimal("40.00"),
            id_currency=currency_eur.id,
            description="Uncategorized group reimbursement",
        )
        db.add_all([payment, reimb])
        db.flush()

        create_group(db, "Uncat Group", [payment, reimb], wallet_account_ids)
        # No category splits on group → net expense = 60 should appear as uncategorized

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["id_category"] is None  # uncategorized
        assert Decimal(str(items[0]["amount"])) == Decimal("60.00")

    def test_group_with_multiple_category_splits(
        self, client, auth_headers, db, wallet_with_accounts,
        account_checking, external_account, currency_eur,
        category_food, category_salary, wallet_account_ids,
    ):
        """A group with multiple category splits allocates correctly."""
        payment = Transaction(
            external_id="grp-pay-4",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 10),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            description="Multi-cat group payment",
        )
        reimb = Transaction(
            external_id="grp-reimb-4",
            id_source=external_account.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 3, 15),
            amount=Decimal("40.00"),
            id_currency=currency_eur.id,
            description="Multi-cat reimbursement",
        )
        db.add_all([payment, reimb])
        db.flush()

        group = create_group(db, "Multi-cat", [payment, reimb], wallet_account_ids)
        # Net expense = 60, split: Food=40, Salary=20
        categorize_group(db, group, category_food, Decimal("40.00"))
        categorize_group(db, group, category_salary, Decimal("20.00"))

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        amounts_by_cat = {i["category_name"]: Decimal(str(i["amount"])) for i in items}
        assert amounts_by_cat["Food"] == Decimal("40.00")
        assert amounts_by_cat["Salary"] == Decimal("20.00")
        assert len(items) == 2

    def test_internal_group_excluded_from_stats(
        self, client, auth_headers, db, wallet_with_accounts,
        account_checking, account_savings, currency_eur, category_food,
        wallet_account_ids,
    ):
        """A group with only wallet-internal transactions must be excluded."""
        t1 = Transaction(
            external_id="int-grp-1",
            id_source=account_checking.id,
            id_dest=account_savings.id,
            date=datetime.date(2024, 3, 10),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            description="Internal transfer",
        )
        t2 = Transaction(
            external_id="int-grp-2",
            id_source=account_savings.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 3, 15),
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            description="Internal return",
        )
        db.add_all([t1, t2])
        db.flush()

        group = create_group(db, "Internal", [t1, t2], wallet_account_ids)
        categorize_group(db, group, category_food, Decimal("50.00"))

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_group_plus_individual_same_category(
        self, client, auth_headers, db, wallet_with_accounts,
        account_checking, external_account, currency_eur, category_food,
        wallet_account_ids,
    ):
        """Group and individual transaction in same category should sum correctly."""
        # Group: net expense = €60
        payment = Transaction(
            external_id="grp-pay-5",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 10),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            description="Group payment",
        )
        reimb = Transaction(
            external_id="grp-reimb-5",
            id_source=external_account.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 3, 15),
            amount=Decimal("40.00"),
            id_currency=currency_eur.id,
            description="Group reimbursement",
        )
        db.add_all([payment, reimb])
        db.flush()

        group = create_group(db, "Group", [payment, reimb], wallet_account_ids)
        categorize_group(db, group, category_food, Decimal("60.00"))

        # Individual: €30 food
        solo = Transaction(
            external_id="solo-food-1",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 20),
            amount=Decimal("30.00"),
            id_currency=currency_eur.id,
            description="Solo food",
        )
        db.add(solo)
        db.flush()
        categorize(db, solo, category_food)

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["category_name"] == "Food"
        assert Decimal(str(items[0]["amount"])) == Decimal("90.00")

    def test_group_with_period_bucket_month(
        self, client, auth_headers, db, wallet_with_accounts,
        account_checking, external_account, currency_eur, category_food,
        wallet_account_ids,
    ):
        """Group should appear in the period of its earliest transaction date."""
        payment = Transaction(
            external_id="grp-pay-6",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 10),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            description="March payment",
        )
        reimb = Transaction(
            external_id="grp-reimb-6",
            id_source=external_account.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 4, 5),
            amount=Decimal("40.00"),
            id_currency=currency_eur.id,
            description="April reimbursement",
        )
        db.add_all([payment, reimb])
        db.flush()

        group = create_group(db, "Cross-month", [payment, reimb], wallet_account_ids)
        categorize_group(db, group, category_food, Decimal("60.00"))

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            params={"period_bucket": "month"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        # Group should appear in March (earliest transaction)
        assert len(items) == 1
        assert items[0]["period_year"] == 2024
        assert items[0]["period_month"] == 3
        assert Decimal(str(items[0]["amount"])) == Decimal("60.00")

    def test_group_date_filter_includes_if_any_tx_matches(
        self, client, auth_headers, db, wallet_with_accounts,
        account_checking, external_account, currency_eur, category_food,
        wallet_account_ids,
    ):
        """Group included if any member transaction falls in date range."""
        payment = Transaction(
            external_id="grp-pay-7",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 10),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            description="March payment",
        )
        reimb = Transaction(
            external_id="grp-reimb-7",
            id_source=external_account.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 4, 5),
            amount=Decimal("40.00"),
            id_currency=currency_eur.id,
            description="April reimbursement",
        )
        db.add_all([payment, reimb])
        db.flush()

        group = create_group(db, "Cross-month", [payment, reimb], wallet_account_ids)
        categorize_group(db, group, category_food, Decimal("60.00"))

        # Filter for March only - group has a tx in March so should be included
        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/per-category",
            params={"date_from": "2024-03-01", "date_to": "2024-03-31"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert Decimal(str(items[0]["amount"])) == Decimal("60.00")


class TestIncomeExpenseWithGroups:
    """Income/expense stats must handle groups via effective_amount."""

    def test_group_net_expense_in_income_expense(
        self, client, auth_headers, db, wallet_with_accounts,
        account_checking, external_account, currency_eur,
        wallet_account_ids,
    ):
        """Group shows net expense via effective_amount mechanism."""
        payment = Transaction(
            external_id="ie-grp-pay",
            id_source=account_checking.id,
            id_dest=external_account.id,
            date=datetime.date(2024, 3, 10),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            description="Group payment",
        )
        reimb = Transaction(
            external_id="ie-grp-reimb",
            id_source=external_account.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 3, 15),
            amount=Decimal("40.00"),
            id_currency=currency_eur.id,
            description="Reimbursement",
        )
        db.add_all([payment, reimb])
        db.flush()

        create_group(db, "IE Group", [payment, reimb], wallet_account_ids)

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/income-expense",
            params={"year": 2024},
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        # Net expense = 100 - 40 = 60, income from reimbursement = 0 (effective=0)
        assert Decimal(str(items[0]["expense"])) == Decimal("60.00")
        assert Decimal(str(items[0]["income"])) == Decimal("0")

    def test_internal_group_excluded_from_income_expense(
        self, client, auth_headers, db, wallet_with_accounts,
        account_checking, account_savings, currency_eur,
        wallet_account_ids,
    ):
        """Group with only internal transactions should not appear in income/expense."""
        t1 = Transaction(
            external_id="ie-int-1",
            id_source=account_checking.id,
            id_dest=account_savings.id,
            date=datetime.date(2024, 3, 10),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            description="Internal 1",
        )
        t2 = Transaction(
            external_id="ie-int-2",
            id_source=account_savings.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 3, 15),
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            description="Internal 2",
        )
        db.add_all([t1, t2])
        db.flush()

        create_group(db, "Internal", [t1, t2], wallet_account_ids)

        r = client.get(
            f"/api/v2/wallets/{wallet_with_accounts.id}/stats/income-expense",
            params={"year": 2024},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["items"] == []
