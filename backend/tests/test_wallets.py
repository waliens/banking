"""Tests for wallet endpoints."""

import pytest


class TestListWallets:
    def test_list_empty(self, client, auth_headers):
        r = client.get("/api/v2/wallets", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []


class TestCreateWallet:
    def test_create_wallet(self, client, auth_headers, account_checking, account_savings):
        r = client.post(
            "/api/v2/wallets",
            json={
                "name": "Personal",
                "description": "My main wallet",
                "accounts": [
                    {"id_account": account_checking.id, "contribution_ratio": 1.0},
                    {"id_account": account_savings.id, "contribution_ratio": 0.5},
                ],
            },
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Personal"
        assert len(data["accounts"]) == 2

    def test_create_empty_name(self, client, auth_headers, account_checking):
        r = client.post(
            "/api/v2/wallets",
            json={"name": "  ", "accounts": [{"id_account": account_checking.id}]},
            headers=auth_headers,
        )
        assert r.status_code == 400

    def test_create_no_accounts(self, client, auth_headers):
        r = client.post(
            "/api/v2/wallets",
            json={"name": "Empty", "accounts": []},
            headers=auth_headers,
        )
        assert r.status_code == 400

    def test_create_invalid_ratio(self, client, auth_headers, account_checking):
        r = client.post(
            "/api/v2/wallets",
            json={"name": "Bad", "accounts": [{"id_account": account_checking.id, "contribution_ratio": 1.5}]},
            headers=auth_headers,
        )
        assert r.status_code == 400


class TestGetWallet:
    def test_get_existing(self, client, auth_headers, account_checking):
        create_r = client.post(
            "/api/v2/wallets",
            json={"name": "Test", "accounts": [{"id_account": account_checking.id}]},
            headers=auth_headers,
        )
        wallet_id = create_r.json()["id"]

        r = client.get(f"/api/v2/wallets/{wallet_id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Test"

    def test_get_not_found(self, client, auth_headers):
        r = client.get("/api/v2/wallets/99999", headers=auth_headers)
        assert r.status_code == 404


class TestUpdateWallet:
    def test_update_name(self, client, auth_headers, account_checking):
        create_r = client.post(
            "/api/v2/wallets",
            json={"name": "Old", "accounts": [{"id_account": account_checking.id}]},
            headers=auth_headers,
        )
        wallet_id = create_r.json()["id"]

        r = client.put(
            f"/api/v2/wallets/{wallet_id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "New Name"

    def test_update_accounts(self, client, auth_headers, account_checking, account_savings):
        create_r = client.post(
            "/api/v2/wallets",
            json={"name": "W", "accounts": [{"id_account": account_checking.id}]},
            headers=auth_headers,
        )
        wallet_id = create_r.json()["id"]

        r = client.put(
            f"/api/v2/wallets/{wallet_id}",
            json={
                "accounts": [
                    {"id_account": account_checking.id, "contribution_ratio": 1.0},
                    {"id_account": account_savings.id, "contribution_ratio": 0.5},
                ]
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert len(r.json()["accounts"]) == 2


class TestDeleteWallet:
    def test_delete(self, client, auth_headers, account_checking):
        create_r = client.post(
            "/api/v2/wallets",
            json={"name": "Temp", "accounts": [{"id_account": account_checking.id}]},
            headers=auth_headers,
        )
        wallet_id = create_r.json()["id"]

        r = client.delete(f"/api/v2/wallets/{wallet_id}", headers=auth_headers)
        assert r.status_code == 204

        r2 = client.get(f"/api/v2/wallets/{wallet_id}", headers=auth_headers)
        assert r2.status_code == 404

    def test_delete_not_found(self, client, auth_headers):
        r = client.delete("/api/v2/wallets/99999", headers=auth_headers)
        assert r.status_code == 404


class TestWalletTransactionFiltering:
    """Test that the wallet filter on transactions works correctly."""

    def test_filter_transactions_by_wallet(
        self, client, auth_headers, db, account_checking, account_savings, sample_transaction
    ):
        # create a wallet with just checking
        create_r = client.post(
            "/api/v2/wallets",
            json={"name": "Checking Only", "accounts": [{"id_account": account_checking.id}]},
            headers=auth_headers,
        )
        wallet_id = create_r.json()["id"]

        r = client.get(f"/api/v2/transactions?wallet={wallet_id}", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1  # sample_transaction has checking as source
