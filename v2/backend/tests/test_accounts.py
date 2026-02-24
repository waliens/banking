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

    def test_list_accounts_search_by_name(self, client, auth_headers, account_checking, account_savings):
        r = client.get("/api/v2/accounts?search=Check", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["name"] == "Checking"

    def test_list_accounts_search_by_number(self, client, auth_headers, account_checking, account_savings):
        r = client.get("/api/v2/accounts?search=1234", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["number"] == "BE1234"

    def test_list_accounts_search_no_match(self, client, auth_headers, account_checking, account_savings):
        r = client.get("/api/v2/accounts?search=NonExistent", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 0


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


class TestMergeSuggestions:
    def test_similar_names_returns_suggestion(self, client, auth_headers, db, currency_eur):
        a = Account(
            name="John Doe",
            number="BE11110000",
            initial_balance=0,
            id_currency=currency_eur.id,
            is_active=True,
        )
        b = Account(
            name="John Doee",
            number="BE22220000",
            initial_balance=0,
            id_currency=currency_eur.id,
            is_active=True,
        )
        db.add_all([a, b])
        db.flush()

        r = client.get("/api/v2/accounts/merge-suggestions", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        ids_in_suggestions = set()
        for s in data:
            ids_in_suggestions.add(s["account_a"]["id"])
            ids_in_suggestions.add(s["account_b"]["id"])
        assert a.id in ids_in_suggestions
        assert b.id in ids_in_suggestions

    def test_no_similar_accounts_returns_empty(self, client, auth_headers, db, currency_eur):
        a = Account(
            name="Alpha Corp",
            number="BE00001111",
            initial_balance=0,
            id_currency=currency_eur.id,
            is_active=True,
        )
        b = Account(
            name="Zebra Inc",
            number="FR99998888",
            initial_balance=0,
            id_currency=currency_eur.id,
            is_active=True,
        )
        db.add_all([a, b])
        db.flush()

        r = client.get("/api/v2/accounts/merge-suggestions", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []


class TestRemoveAlias:
    def test_remove_alias_success(self, client, auth_headers, db, account_checking):
        alias = AccountAlias(name="Old Checking", number="BE0000", id_account=account_checking.id)
        db.add(alias)
        db.flush()

        r = client.delete(
            f"/api/v2/accounts/{account_checking.id}/aliases/{alias.id}",
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["msg"] == "alias removed"
        assert db.get(AccountAlias, alias.id) is None

    def test_remove_alias_with_promote(self, client, auth_headers, db, account_checking):
        alias = AccountAlias(name="Promoted Account", number="BE9999", id_account=account_checking.id)
        db.add(alias)
        db.flush()
        alias_id = alias.id

        r = client.delete(
            f"/api/v2/accounts/{account_checking.id}/aliases/{alias_id}?promote=true",
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["msg"] == "alias promoted to account"
        # Alias should be deleted
        assert db.get(AccountAlias, alias_id) is None
        # A new account with the alias name should exist
        from sqlalchemy import select

        new_acc = db.execute(select(Account).where(Account.name == "Promoted Account")).scalar_one_or_none()
        assert new_acc is not None
        assert new_acc.number == "BE9999"

    def test_remove_nonexistent_alias(self, client, auth_headers, account_checking):
        r = client.delete(
            f"/api/v2/accounts/{account_checking.id}/aliases/99999",
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_remove_alias_wrong_account(self, client, auth_headers, db, account_checking, account_savings):
        alias = AccountAlias(name="Belongs to Savings", number="BE7777", id_account=account_savings.id)
        db.add(alias)
        db.flush()

        # Try to delete alias via the checking account (wrong account)
        r = client.delete(
            f"/api/v2/accounts/{account_checking.id}/aliases/{alias.id}",
            headers=auth_headers,
        )
        assert r.status_code == 404


class TestUpdateAccountNameNumber:
    def test_update_name(self, client, auth_headers, account_checking):
        r = client.put(
            f"/api/v2/accounts/{account_checking.id}",
            json={"name": "My Checking Account"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "My Checking Account"

    def test_update_number(self, client, auth_headers, account_checking):
        r = client.put(
            f"/api/v2/accounts/{account_checking.id}",
            json={"number": "BE9999"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["number"] == "BE9999"
