"""Tests for import endpoints."""

import datetime
from decimal import Decimal

import pytest
from app.models import ImportRecord, Transaction


class TestListImports:
    def test_list_empty(self, client, auth_headers, currency_eur):
        r = client.get("/api/v2/imports", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_with_records(self, client, auth_headers, import_record):
        r = client.get("/api/v2/imports", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["format"] == "belfius"
        assert data[0]["filenames"] == ["test.csv"]
        assert data[0]["total_transactions"] == 3
        assert data[0]["new_transactions"] == 2
        assert data[0]["duplicate_transactions"] == 1

    def test_list_unauthenticated(self, client):
        r = client.get("/api/v2/imports")
        assert r.status_code == 401

    def test_list_pagination(self, client, auth_headers, db, currency_eur):
        for i in range(5):
            ir = ImportRecord(
                format="belfius",
                filenames=[f"file_{i}.csv"],
                total_transactions=i,
                new_transactions=i,
                duplicate_transactions=0,
                skipped_transactions=0,
                new_accounts=0,
                auto_tagged=0,
            )
            db.add(ir)
        db.flush()

        r = client.get("/api/v2/imports?start=0&count=2", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 2

        r2 = client.get("/api/v2/imports?start=2&count=2", headers=auth_headers)
        assert r2.status_code == 200
        assert len(r2.json()) == 2

        r3 = client.get("/api/v2/imports?start=4&count=2", headers=auth_headers)
        assert r3.status_code == 200
        assert len(r3.json()) == 1


class TestGetImport:
    def test_get_existing(self, client, auth_headers, import_record):
        r = client.get(f"/api/v2/imports/{import_record.id}", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == import_record.id
        assert data["format"] == "belfius"
        assert data["filenames"] == ["test.csv"]
        assert data["new_transactions"] == 2
        assert data["date_earliest"] == "2024-06-01"
        assert data["date_latest"] == "2024-06-30"

    def test_get_not_found(self, client, auth_headers, currency_eur):
        r = client.get("/api/v2/imports/99999", headers=auth_headers)
        assert r.status_code == 404


class TestImportTransactions:
    def test_returns_linked_transactions(self, client, auth_headers, import_record):
        r = client.get(f"/api/v2/imports/{import_record.id}/transactions", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        descriptions = {t["description"] for t in data}
        assert descriptions == {"Import test 0", "Import test 1"}

    def test_not_found(self, client, auth_headers, currency_eur):
        r = client.get("/api/v2/imports/99999/transactions", headers=auth_headers)
        assert r.status_code == 404

    def test_does_not_return_unlinked_transactions(
        self, client, auth_headers, db, import_record, account_checking, currency_eur
    ):
        # Create a transaction NOT linked to the import
        t = Transaction(
            external_id="unlinked-tx",
            id_source=account_checking.id,
            date=datetime.date(2024, 6, 15),
            amount=Decimal("99.00"),
            id_currency=currency_eur.id,
            data_source="manual",
            description="Unlinked",
        )
        db.add(t)
        db.flush()

        r = client.get(f"/api/v2/imports/{import_record.id}/transactions", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert all(t["description"] != "Unlinked" for t in data)

    def test_duplicate_only_filter(
        self, client, auth_headers, db, import_record, account_checking, account_savings, currency_eur
    ):
        """duplicate_only=true returns only transactions marked as duplicates at import time."""
        # Create a duplicate transaction linked to the import
        dup = Transaction(
            external_id="dup-tx",
            id_source=account_checking.id,
            id_dest=account_savings.id,
            date=datetime.date(2024, 6, 15),
            amount=Decimal("25.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
            description="Duplicate",
            id_import=import_record.id,
            id_duplicate_of=1,
        )
        db.add(dup)
        db.flush()

        r = client.get(
            f"/api/v2/imports/{import_record.id}/transactions?duplicate_only=true",
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["description"] == "Duplicate"

    def test_auto_tagged_only_filter(
        self, client, auth_headers, db, import_record, account_checking, account_savings, currency_eur
    ):
        """auto_tagged_only=true returns only transactions auto-tagged at import time."""
        # Mark one existing import transaction as auto-tagged
        txs = db.query(Transaction).filter(Transaction.id_import == import_record.id).all()
        txs[0].auto_tagged_at_import = True
        db.flush()

        r = client.get(
            f"/api/v2/imports/{import_record.id}/transactions?auto_tagged_only=true",
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["description"] == txs[0].description


class TestImportAccounts:
    def test_returns_accounts(self, client, auth_headers, import_record, account_checking, account_savings):
        r = client.get(f"/api/v2/imports/{import_record.id}/accounts", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        account_names = {a["name"] for a in data}
        assert "Checking" in account_names
        assert "Savings" in account_names

    def test_not_found(self, client, auth_headers, currency_eur):
        r = client.get("/api/v2/imports/99999/accounts", headers=auth_headers)
        assert r.status_code == 404

    def test_empty_import_returns_no_accounts(self, client, auth_headers, db, currency_eur):
        ir = ImportRecord(
            format="belfius",
            filenames=["empty.csv"],
            total_transactions=0,
            new_transactions=0,
            duplicate_transactions=0,
            skipped_transactions=0,
            new_accounts=0,
            auto_tagged=0,
        )
        db.add(ir)
        db.flush()

        r = client.get(f"/api/v2/imports/{ir.id}/accounts", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []
