"""Tests for category endpoints."""

import pytest


class TestListCategories:
    def test_list_empty(self, client, auth_headers):
        r = client.get("/api/v2/categories", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_with_categories(self, client, auth_headers, category_food, category_salary):
        r = client.get("/api/v2/categories", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2


class TestGetCategory:
    def test_get_existing(self, client, auth_headers, category_food):
        r = client.get(f"/api/v2/categories/{category_food.id}", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Food"
        assert data["color"] == "#FF0000"
        assert data["is_income"] is False

    def test_get_not_found(self, client, auth_headers):
        r = client.get("/api/v2/categories/99999", headers=auth_headers)
        assert r.status_code == 404


class TestCreateCategory:
    def test_create_root_category(self, client, auth_headers):
        r = client.post(
            "/api/v2/categories",
            json={"name": "Transport", "color": "#0000FF"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Transport"
        assert data["id_parent"] is None
        assert data["sort_order"] == 0
        assert data["is_income"] is False

    def test_create_child_category(self, client, auth_headers, category_food):
        r = client.post(
            "/api/v2/categories",
            json={"name": "Restaurants", "color": "#FF1111", "id_parent": category_food.id},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["id_parent"] == category_food.id

    def test_create_income_category(self, client, auth_headers):
        r = client.post(
            "/api/v2/categories",
            json={"name": "Bonus", "color": "#00FF00", "is_income": True},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["is_income"] is True

    def test_create_invalid_color(self, client, auth_headers):
        r = client.post(
            "/api/v2/categories",
            json={"name": "Bad", "color": "not-a-color"},
            headers=auth_headers,
        )
        assert r.status_code == 400

    def test_create_empty_name(self, client, auth_headers):
        r = client.post(
            "/api/v2/categories",
            json={"name": "", "color": "#123456"},
            headers=auth_headers,
        )
        assert r.status_code == 400


class TestUpdateCategory:
    def test_update_name(self, client, auth_headers, category_food):
        r = client.put(
            f"/api/v2/categories/{category_food.id}",
            json={"name": "Food & Drink"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Food & Drink"

    def test_update_color(self, client, auth_headers, category_food):
        r = client.put(
            f"/api/v2/categories/{category_food.id}",
            json={"color": "#AABBCC"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["color"] == "#AABBCC"

    def test_update_not_found(self, client, auth_headers):
        r = client.put("/api/v2/categories/99999", json={"name": "X"}, headers=auth_headers)
        assert r.status_code == 404


class TestDeleteCategory:
    def test_delete_leaf(self, client, auth_headers, category_food):
        r = client.delete(f"/api/v2/categories/{category_food.id}", headers=auth_headers)
        assert r.status_code == 204

        # should be gone
        r2 = client.get(f"/api/v2/categories/{category_food.id}", headers=auth_headers)
        assert r2.status_code == 404

    def test_delete_parent_reparents_children(self, client, auth_headers, db, category_food, category_child):
        """Deleting a parent should reparent its children to the grandparent (None for root)."""
        r = client.delete(f"/api/v2/categories/{category_food.id}", headers=auth_headers)
        assert r.status_code == 204

        # child should now be a root category
        db.expire_all()
        r2 = client.get(f"/api/v2/categories/{category_child.id}", headers=auth_headers)
        assert r2.status_code == 200
        assert r2.json()["id_parent"] is None

    def test_delete_unlinks_transactions(self, client, auth_headers, db, category_food, sample_transaction):
        # assign category to transaction
        sample_transaction.id_category = category_food.id
        db.flush()

        r = client.delete(f"/api/v2/categories/{category_food.id}", headers=auth_headers)
        assert r.status_code == 204

        # transaction should have no category
        db.expire_all()
        r2 = client.get(f"/api/v2/transactions/{sample_transaction.id}", headers=auth_headers)
        assert r2.json()["id_category"] is None

    def test_delete_not_found(self, client, auth_headers):
        r = client.delete("/api/v2/categories/99999", headers=auth_headers)
        assert r.status_code == 404
