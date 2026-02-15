"""Tests for transaction endpoints."""

import datetime
from decimal import Decimal

import pytest
from app.models import Transaction


class TestListTransactions:
    def test_list_empty(self, client, auth_headers, currency_eur):
        r = client.get("/api/v2/transactions", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_with_transactions(self, client, auth_headers, sample_transaction):
        r = client.get("/api/v2/transactions", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["description"] == "Test transfer"

    def test_list_pagination(self, client, auth_headers, db, currency_eur, account_checking):
        # create 5 transactions
        for i in range(5):
            db.add(
                Transaction(
                    external_id=f"tx-page-{i}",
                    id_source=account_checking.id,
                    date=datetime.date(2024, 1, i + 1),
                    amount=Decimal("10.00"),
                    id_currency=currency_eur.id,
                    data_source="manual",
                    description=f"Tx {i}",
                )
            )
        db.flush()

        r = client.get("/api/v2/transactions?start=0&count=2", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 2

        r2 = client.get("/api/v2/transactions?start=2&count=2", headers=auth_headers)
        assert r2.status_code == 200
        assert len(r2.json()) == 2

        r3 = client.get("/api/v2/transactions?start=4&count=2", headers=auth_headers)
        assert r3.status_code == 200
        assert len(r3.json()) == 1

    def test_list_sort_asc(self, client, auth_headers, db, currency_eur, account_checking):
        for i, day in enumerate([15, 5, 25]):
            db.add(
                Transaction(
                    external_id=f"tx-sort-{i}",
                    id_source=account_checking.id,
                    date=datetime.date(2024, 1, day),
                    amount=Decimal("10.00"),
                    id_currency=currency_eur.id,
                    data_source="manual",
                )
            )
        db.flush()

        r = client.get("/api/v2/transactions?order=asc", headers=auth_headers)
        dates = [t["date"] for t in r.json()]
        assert dates == sorted(dates)

    def test_filter_by_account(self, client, auth_headers, sample_transaction, account_checking):
        r = client.get(f"/api/v2/transactions?account={account_checking.id}", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_filter_by_labeled(self, client, auth_headers, db, sample_transaction, category_food):
        # unlabeled
        r = client.get("/api/v2/transactions?labeled=false", headers=auth_headers)
        assert len(r.json()) == 1

        r2 = client.get("/api/v2/transactions?labeled=true", headers=auth_headers)
        assert len(r2.json()) == 0

        # label it
        sample_transaction.id_category = category_food.id
        db.flush()

        r3 = client.get("/api/v2/transactions?labeled=true", headers=auth_headers)
        assert len(r3.json()) == 1

    def test_filter_by_date_range(self, client, auth_headers, sample_transaction):
        r = client.get(
            "/api/v2/transactions?date_from=2024-06-01&date_to=2024-06-30",
            headers=auth_headers,
        )
        assert len(r.json()) == 1

        r2 = client.get(
            "/api/v2/transactions?date_from=2024-07-01&date_to=2024-07-31",
            headers=auth_headers,
        )
        assert len(r2.json()) == 0

    def test_filter_by_is_reviewed(self, client, auth_headers, sample_transaction):
        r = client.get("/api/v2/transactions?is_reviewed=false", headers=auth_headers)
        assert len(r.json()) == 1

        r2 = client.get("/api/v2/transactions?is_reviewed=true", headers=auth_headers)
        assert len(r2.json()) == 0

    def test_filter_by_search_query(self, client, auth_headers, sample_transaction):
        r = client.get("/api/v2/transactions?search_query=transfer", headers=auth_headers)
        assert len(r.json()) == 1

        r2 = client.get("/api/v2/transactions?search_query=nonexistent", headers=auth_headers)
        assert len(r2.json()) == 0

    def test_excludes_duplicates_by_default(
        self, client, auth_headers, db, sample_transaction, currency_eur, account_checking
    ):
        dup = Transaction(
            external_id="tx-dup",
            id_source=account_checking.id,
            date=datetime.date(2024, 6, 15),
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            data_source="manual",
            id_duplicate_of=sample_transaction.id,
        )
        db.add(dup)
        db.flush()

        r = client.get("/api/v2/transactions", headers=auth_headers)
        assert len(r.json()) == 1  # only the original

        r2 = client.get("/api/v2/transactions?duplicate_only=true", headers=auth_headers)
        assert len(r2.json()) == 1  # only the duplicate


class TestCountTransactions:
    def test_count(self, client, auth_headers, sample_transaction):
        r = client.get("/api/v2/transactions/count", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["count"] == 1

    def test_count_with_filter(self, client, auth_headers, sample_transaction):
        r = client.get("/api/v2/transactions/count?labeled=true", headers=auth_headers)
        assert r.json()["count"] == 0


class TestGetTransaction:
    def test_get_existing(self, client, auth_headers, sample_transaction):
        r = client.get(f"/api/v2/transactions/{sample_transaction.id}", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["description"] == "Test transfer"
        assert data["amount"] == "50.00"
        assert data["source"] is not None
        assert data["dest"] is not None

    def test_get_not_found(self, client, auth_headers, currency_eur):
        r = client.get("/api/v2/transactions/99999", headers=auth_headers)
        assert r.status_code == 404


class TestCreateTransaction:
    def test_create_manual(self, client, auth_headers, account_checking, account_savings, currency_eur):
        r = client.post(
            "/api/v2/transactions",
            json={
                "id_source": account_checking.id,
                "id_dest": account_savings.id,
                "date": "2024-07-01",
                "amount": "100.00",
                "id_currency": currency_eur.id,
                "description": "Monthly savings",
            },
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["description"] == "Monthly savings"
        assert data["data_source"] == "manual"
        assert data["external_id"] is not None

    def test_create_negative_amount_flips_accounts(
        self, client, auth_headers, account_checking, account_savings, currency_eur
    ):
        r = client.post(
            "/api/v2/transactions",
            json={
                "id_source": account_checking.id,
                "id_dest": account_savings.id,
                "date": "2024-07-01",
                "amount": "-50.00",
                "id_currency": currency_eur.id,
            },
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert Decimal(data["amount"]) == Decimal("50.00")
        # accounts should be flipped
        assert data["id_source"] == account_savings.id
        assert data["id_dest"] == account_checking.id

    def test_create_with_category_marks_reviewed(
        self, client, auth_headers, account_checking, currency_eur, category_food
    ):
        r = client.post(
            "/api/v2/transactions",
            json={
                "date": "2024-07-01",
                "amount": "25.00",
                "id_currency": currency_eur.id,
                "id_category": category_food.id,
                "id_source": account_checking.id,
            },
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["is_reviewed"] is True


class TestUpdateTransaction:
    def test_update_description(self, client, auth_headers, sample_transaction):
        r = client.put(
            f"/api/v2/transactions/{sample_transaction.id}",
            json={"description": "Updated"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["description"] == "Updated"

    def test_cannot_update_non_manual(self, client, auth_headers, db, sample_transaction):
        sample_transaction.data_source = "belfius"
        db.flush()

        r = client.put(
            f"/api/v2/transactions/{sample_transaction.id}",
            json={"description": "X"},
            headers=auth_headers,
        )
        assert r.status_code == 400


class TestDeleteTransaction:
    def test_delete_manual(self, client, auth_headers, sample_transaction):
        r = client.delete(f"/api/v2/transactions/{sample_transaction.id}", headers=auth_headers)
        assert r.status_code == 204

    def test_cannot_delete_non_manual(self, client, auth_headers, db, sample_transaction):
        sample_transaction.data_source = "belfius"
        db.flush()

        r = client.delete(f"/api/v2/transactions/{sample_transaction.id}", headers=auth_headers)
        assert r.status_code == 400


class TestSetCategory:
    def test_set_category(self, client, auth_headers, sample_transaction, category_food):
        r = client.put(
            f"/api/v2/transactions/{sample_transaction.id}/category/{category_food.id}",
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["id_category"] == category_food.id
        assert data["is_reviewed"] is True


class TestBatchTag:
    def test_batch_tag(
        self, client, auth_headers, db, sample_transaction, category_food, currency_eur, account_checking
    ):
        t2 = Transaction(
            external_id="tx-batch-2",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("20.00"),
            id_currency=currency_eur.id,
            data_source="manual",
        )
        db.add(t2)
        db.flush()

        r = client.put(
            "/api/v2/transactions/tag",
            json={
                "categories": [
                    {"id_transaction": sample_transaction.id, "id_category": category_food.id},
                    {"id_transaction": t2.id, "id_category": category_food.id},
                ]
            },
            headers=auth_headers,
        )
        assert r.status_code == 200


class TestDuplicates:
    def test_get_duplicate_candidates(
        self, client, auth_headers, db, sample_transaction, currency_eur, account_checking, account_savings
    ):
        # create a near-duplicate (same amount, accounts, within 7 days)
        candidate = Transaction(
            external_id="tx-dup-cand",
            id_source=account_checking.id,
            id_dest=account_savings.id,
            date=datetime.date(2024, 6, 16),  # 1 day later
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
        )
        db.add(candidate)
        db.flush()

        r = client.get(
            f"/api/v2/transactions/{sample_transaction.id}/duplicate_candidates",
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["id"] == candidate.id

    def test_set_and_unset_duplicate(
        self, client, auth_headers, db, sample_transaction, currency_eur, account_checking
    ):
        child = Transaction(
            external_id="tx-child",
            id_source=account_checking.id,
            date=datetime.date(2024, 6, 15),
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
        )
        db.add(child)
        db.flush()

        # set duplicate
        r = client.put(
            f"/api/v2/transactions/{child.id}/duplicate_of/{sample_transaction.id}",
            headers=auth_headers,
        )
        assert r.status_code == 200

        # unset
        r2 = client.delete(f"/api/v2/transactions/{child.id}/duplicate_of", headers=auth_headers)
        assert r2.status_code == 200

    def test_cannot_set_duplicate_of_duplicate(
        self, client, auth_headers, db, sample_transaction, currency_eur, account_checking
    ):
        parent_dup = Transaction(
            external_id="tx-parent-dup",
            id_source=account_checking.id,
            date=datetime.date(2024, 6, 15),
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
            id_duplicate_of=sample_transaction.id,
        )
        child = Transaction(
            external_id="tx-child-2",
            id_source=account_checking.id,
            date=datetime.date(2024, 6, 15),
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
        )
        db.add_all([parent_dup, child])
        db.flush()

        r = client.put(
            f"/api/v2/transactions/{child.id}/duplicate_of/{parent_dup.id}",
            headers=auth_headers,
        )
        assert r.status_code == 400
