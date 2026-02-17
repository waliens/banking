"""Tests for auth endpoints: login, refresh, logout, user CRUD, preferences."""

import pytest
from app.models import User


class TestLogin:
    def test_login_success(self, client, user):
        r = client.post("/api/v2/auth/login", json={"username": "testuser", "password": "testpass123"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # refresh token should be in cookies
        assert "refresh_token" in r.cookies

    def test_login_wrong_password(self, client, user):
        r = client.post("/api/v2/auth/login", json={"username": "testuser", "password": "wrong"})
        assert r.status_code == 401

    def test_login_nonexistent_user(self, client):
        r = client.post("/api/v2/auth/login", json={"username": "nobody", "password": "test"})
        assert r.status_code == 401

    def test_login_empty_body(self, client):
        r = client.post("/api/v2/auth/login", json={})
        assert r.status_code == 422


class TestRefresh:
    def test_refresh_with_cookie(self, client, user):
        # login first to get refresh cookie
        login_r = client.post("/api/v2/auth/login", json={"username": "testuser", "password": "testpass123"})
        assert login_r.status_code == 200

        # refresh should work with the cookie set by login
        r = client.post("/api/v2/auth/refresh")
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_refresh_without_cookie(self, client):
        r = client.post("/api/v2/auth/refresh")
        assert r.status_code == 401


class TestLogout:
    def test_logout(self, client, user):
        client.post("/api/v2/auth/login", json={"username": "testuser", "password": "testpass123"})
        r = client.post("/api/v2/auth/logout")
        assert r.status_code == 200
        assert r.json()["msg"] == "logged out"


class TestGetMe:
    def test_get_me_authenticated(self, client, user, auth_headers):
        r = client.get("/api/v2/auth/me", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "testuser"
        assert data["id"] == user.id
        assert "password_hash" not in data

    def test_get_me_unauthenticated(self, client):
        r = client.get("/api/v2/auth/me")
        assert r.status_code == 401  # no bearer token

    def test_get_me_invalid_token(self, client):
        r = client.get("/api/v2/auth/me", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401


class TestUserCRUD:
    def test_list_users(self, client, user, auth_headers):
        r = client.get("/api/v2/auth/users", headers=auth_headers)
        assert r.status_code == 200
        users = r.json()
        assert len(users) >= 1
        assert any(u["username"] == "testuser" for u in users)

    def test_create_user(self, client, user, auth_headers):
        r = client.post(
            "/api/v2/auth/users",
            json={"username": "newuser", "password": "newpass456"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["username"] == "newuser"

    def test_create_user_duplicate_username(self, client, user, auth_headers):
        r = client.post(
            "/api/v2/auth/users",
            json={"username": "testuser", "password": "whatever"},
            headers=auth_headers,
        )
        assert r.status_code == 409

    def test_update_user(self, client, user, auth_headers):
        r = client.put(
            f"/api/v2/auth/users/{user.id}",
            json={"username": "updated_name"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["username"] == "updated_name"

    def test_update_user_password(self, client, user, auth_headers):
        r = client.put(
            f"/api/v2/auth/users/{user.id}",
            json={"password": "new_secure_pass"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        # should be able to login with the new password
        r2 = client.post("/api/v2/auth/login", json={"username": "testuser", "password": "new_secure_pass"})
        assert r2.status_code == 200

    def test_update_nonexistent_user(self, client, user, auth_headers):
        r = client.put(
            "/api/v2/auth/users/99999",
            json={"username": "whatever"},
            headers=auth_headers,
        )
        assert r.status_code == 404


class TestPreferences:
    def test_set_default_wallet(self, client, user, auth_headers, wallet):
        r = client.put(
            "/api/v2/auth/me/preferences",
            json={"default_wallet_id": wallet.id},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["preferences"]["default_wallet_id"] == wallet.id

    def test_clear_default_wallet(self, client, user, auth_headers, wallet):
        # First set a preference
        client.put(
            "/api/v2/auth/me/preferences",
            json={"default_wallet_id": wallet.id},
            headers=auth_headers,
        )
        # Then clear it
        r = client.put(
            "/api/v2/auth/me/preferences",
            json={"default_wallet_id": None},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "default_wallet_id" not in (data["preferences"] or {})

    def test_set_invalid_wallet(self, client, user, auth_headers):
        r = client.put(
            "/api/v2/auth/me/preferences",
            json={"default_wallet_id": 99999},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_preferences_unauthenticated(self, client):
        r = client.put(
            "/api/v2/auth/me/preferences",
            json={"default_wallet_id": 1},
        )
        assert r.status_code == 401
