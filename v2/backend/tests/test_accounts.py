"""Tests for account endpoints."""

import pytest
from decimal import Decimal
from app.models import Account, AccountAlias, Currency


class TestListAccounts:
    def test_list_empty(self, client, auth_headers, currency_eur):
        r = client.get("/api/v2/accounts", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_with_accounts(self, client, auth_headers, account_checking, account_savings):
        r = client.get("/api/v2/accounts", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        names = {a["name"] for a in data}
        assert names == {"Checking", "Savings"}

    def test_list_unauthenticated(self, client):
        r = client.get("/api/v2/accounts")
        assert r.status_code == 401


class TestGetAccount:
    def test_get_existing(self, client, auth_headers, account_checking):
        r = client.get(f"/api/v2/accounts/{account_checking.id}", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Checking"
        assert data["number"] == "BE1234"
        assert data["institution"] == "belfius"
        assert "currency" in data

    def test_get_not_found(self, client, auth_headers, currency_eur):
        r = client.get("/api/v2/accounts/99999", headers=auth_headers)
        assert r.status_code == 404


class TestUpdateAccount:
    def test_update_initial_balance(self, client, auth_headers, account_checking):
        r = client.put(
            f"/api/v2/accounts/{account_checking.id}",
            json={"initial_balance": "2000.00"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert Decimal(r.json()["initial_balance"]) == Decimal("2000.00")

    def test_update_institution(self, client, auth_headers, account_checking):
        r = client.put(
            f"/api/v2/accounts/{account_checking.id}",
            json={"institution": "ing"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["institution"] == "ing"

    def test_deactivate_account(self, client, auth_headers, account_checking):
        r = client.put(
            f"/api/v2/accounts/{account_checking.id}",
            json={"is_active": False},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_update_not_found(self, client, auth_headers, currency_eur):
        r = client.put("/api/v2/accounts/99999", json={"is_active": False}, headers=auth_headers)
        assert r.status_code == 404


class TestAliases:
    def test_add_alias(self, client, auth_headers, account_checking):
        r = client.post(
            f"/api/v2/accounts/{account_checking.id}/aliases",
            json={"name": "Old Name", "number": "BE0000"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Old Name"
        assert r.json()["id_account"] == account_checking.id

    def test_add_duplicate_alias(self, client, auth_headers, account_checking):
        # alias that matches the account's own name/number
        r = client.post(
            f"/api/v2/accounts/{account_checking.id}/aliases",
            json={"name": "Checking", "number": "BE1234"},
            headers=auth_headers,
        )
        assert r.status_code == 409

    def test_add_alias_not_found(self, client, auth_headers, currency_eur):
        r = client.post("/api/v2/accounts/99999/aliases", json={"name": "X"}, headers=auth_headers)
        assert r.status_code == 404


class TestMergeAccounts:
    def test_merge_success(self, client, auth_headers, db, account_checking, account_savings, currency_eur):
        r = client.put(
            "/api/v2/accounts/merge",
            json={"id_alias": account_savings.id, "id_repr": account_checking.id},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == account_checking.id
        # savings should be gone
        assert db.get(Account, account_savings.id) is None

    def test_merge_self(self, client, auth_headers, account_checking):
        r = client.put(
            "/api/v2/accounts/merge",
            json={"id_alias": account_checking.id, "id_repr": account_checking.id},
            headers=auth_headers,
        )
        assert r.status_code == 400

    def test_merge_with_transactions_between(
        self, client, auth_headers, sample_transaction, account_checking, account_savings
    ):
        # sample_transaction goes from checking to savings
        r = client.put(
            "/api/v2/accounts/merge",
            json={"id_alias": account_savings.id, "id_repr": account_checking.id},
            headers=auth_headers,
        )
        assert r.status_code == 400
        assert "transactions between" in r.json()["detail"]
