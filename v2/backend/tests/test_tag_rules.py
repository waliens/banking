"""Tests for tag rules CRUD and apply endpoints."""

import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Account, Category, Currency, TagRule, Transaction, User


@pytest.fixture
def category_transport(db: Session, category_food: Category) -> Category:
    c = Category(name="Transport", color="#0000FF", sort_order=2, is_income=False)
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def tag_rule(db: Session, category_food: Category) -> TagRule:
    rule = TagRule(
        name="Grocery rule",
        id_category=category_food.id,
        match_description="colruyt",
        priority=10,
        is_active=True,
    )
    db.add(rule)
    db.flush()
    return rule


class TestListTagRules:
    def test_list_empty(self, client, auth_headers, currency_eur):
        resp = client.get("/api/v2/tag-rules", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_rules(self, client, auth_headers, tag_rule):
        resp = client.get("/api/v2/tag-rules", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Grocery rule"
        assert data[0]["category"]["name"] == "Food"

    def test_list_ordered_by_priority(self, client, auth_headers, db, category_food, category_transport):
        r1 = TagRule(name="Low", id_category=category_food.id, priority=1, is_active=True)
        r2 = TagRule(name="High", id_category=category_transport.id, priority=100, is_active=True)
        db.add_all([r1, r2])
        db.flush()

        resp = client.get("/api/v2/tag-rules", headers=auth_headers)
        data = resp.json()
        assert data[0]["name"] == "High"
        assert data[1]["name"] == "Low"


class TestCreateTagRule:
    def test_create(self, client, auth_headers, category_food):
        resp = client.post(
            "/api/v2/tag-rules",
            headers=auth_headers,
            json={
                "name": "Test rule",
                "id_category": category_food.id,
                "match_description": "test",
                "priority": 5,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test rule"
        assert data["id_category"] == category_food.id
        assert data["match_description"] == "test"
        assert data["priority"] == 5
        assert data["is_active"] is True

    def test_create_with_regex(self, client, auth_headers, category_food):
        resp = client.post(
            "/api/v2/tag-rules",
            headers=auth_headers,
            json={
                "name": "Regex rule",
                "id_category": category_food.id,
                "match_description": "^colruyt.*brussels$",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["match_description"] == "^colruyt.*brussels$"

    def test_create_invalid_regex(self, client, auth_headers, category_food):
        resp = client.post(
            "/api/v2/tag-rules",
            headers=auth_headers,
            json={
                "name": "Bad regex",
                "id_category": category_food.id,
                "match_description": "[invalid",
            },
        )
        assert resp.status_code == 422


class TestGetTagRule:
    def test_get(self, client, auth_headers, tag_rule):
        resp = client.get(f"/api/v2/tag-rules/{tag_rule.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Grocery rule"

    def test_not_found(self, client, auth_headers, currency_eur):
        resp = client.get("/api/v2/tag-rules/999", headers=auth_headers)
        assert resp.status_code == 404


class TestUpdateTagRule:
    def test_update(self, client, auth_headers, tag_rule):
        resp = client.put(
            f"/api/v2/tag-rules/{tag_rule.id}",
            headers=auth_headers,
            json={"name": "Updated rule", "priority": 20},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated rule"
        assert data["priority"] == 20
        assert data["match_description"] == "colruyt"  # unchanged

    def test_update_invalid_regex(self, client, auth_headers, tag_rule):
        resp = client.put(
            f"/api/v2/tag-rules/{tag_rule.id}",
            headers=auth_headers,
            json={"match_description": "[invalid"},
        )
        assert resp.status_code == 422

    def test_not_found(self, client, auth_headers, currency_eur):
        resp = client.put("/api/v2/tag-rules/999", headers=auth_headers, json={"name": "x"})
        assert resp.status_code == 404


class TestDeleteTagRule:
    def test_delete(self, client, auth_headers, tag_rule):
        resp = client.delete(f"/api/v2/tag-rules/{tag_rule.id}", headers=auth_headers)
        assert resp.status_code == 204

        resp = client.get(f"/api/v2/tag-rules/{tag_rule.id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_not_found(self, client, auth_headers, currency_eur):
        resp = client.delete("/api/v2/tag-rules/999", headers=auth_headers)
        assert resp.status_code == 404


class TestApplyTagRules:
    def test_apply_matches_description(self, client, auth_headers, db, tag_rule, account_checking, currency_eur):
        t = Transaction(
            external_id="apply-1",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("10.00"),
            id_currency=currency_eur.id,
            description="Colruyt supermarket",
            is_reviewed=False,
        )
        db.add(t)
        db.flush()

        resp = client.post("/api/v2/tag-rules/apply", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["applied_count"] == 1

        db.refresh(t)
        assert t.id_category == tag_rule.id_category
        assert t.is_reviewed is True

    def test_apply_skips_categorized(
        self, client, auth_headers, db, tag_rule, account_checking, currency_eur, category_salary
    ):
        t = Transaction(
            external_id="apply-2",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("10.00"),
            id_currency=currency_eur.id,
            description="Colruyt supermarket",
            id_category=category_salary.id,
            is_reviewed=True,
        )
        db.add(t)
        db.flush()

        resp = client.post("/api/v2/tag-rules/apply", headers=auth_headers)
        assert resp.json()["applied_count"] == 0

    def test_apply_amount_range(self, client, auth_headers, db, category_food, account_checking, currency_eur):
        rule = TagRule(
            name="Amount rule",
            id_category=category_food.id,
            match_amount_min=Decimal("50.00"),
            match_amount_max=Decimal("100.00"),
            priority=5,
            is_active=True,
        )
        db.add(rule)
        db.flush()

        t_match = Transaction(
            external_id="amt-1",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("75.00"),
            id_currency=currency_eur.id,
            description="Something",
            is_reviewed=False,
        )
        t_no_match = Transaction(
            external_id="amt-2",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("30.00"),
            id_currency=currency_eur.id,
            description="Something else",
            is_reviewed=False,
        )
        db.add_all([t_match, t_no_match])
        db.flush()

        resp = client.post("/api/v2/tag-rules/apply", headers=auth_headers)
        assert resp.json()["applied_count"] == 1

        db.refresh(t_match)
        db.refresh(t_no_match)
        assert t_match.id_category == category_food.id
        assert t_no_match.id_category is None

    def test_apply_account_match(
        self, client, auth_headers, db, category_food, account_checking, account_savings, currency_eur
    ):
        rule = TagRule(
            name="Account rule",
            id_category=category_food.id,
            match_account_from=account_checking.id,
            priority=5,
            is_active=True,
        )
        db.add(rule)
        db.flush()

        t_match = Transaction(
            external_id="acct-1",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("10.00"),
            id_currency=currency_eur.id,
            description="Anything",
            is_reviewed=False,
        )
        t_no_match = Transaction(
            external_id="acct-2",
            id_source=account_savings.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("10.00"),
            id_currency=currency_eur.id,
            description="Anything",
            is_reviewed=False,
        )
        db.add_all([t_match, t_no_match])
        db.flush()

        resp = client.post("/api/v2/tag-rules/apply", headers=auth_headers)
        assert resp.json()["applied_count"] == 1

    def test_apply_priority_ordering(
        self, client, auth_headers, db, category_food, category_transport, account_checking, currency_eur
    ):
        rule_low = TagRule(
            name="Low priority",
            id_category=category_food.id,
            match_description="shop",
            priority=1,
            is_active=True,
        )
        rule_high = TagRule(
            name="High priority",
            id_category=category_transport.id,
            match_description="shop",
            priority=100,
            is_active=True,
        )
        db.add_all([rule_low, rule_high])
        db.flush()

        t = Transaction(
            external_id="prio-1",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("10.00"),
            id_currency=currency_eur.id,
            description="shop around corner",
            is_reviewed=False,
        )
        db.add(t)
        db.flush()

        resp = client.post("/api/v2/tag-rules/apply", headers=auth_headers)
        assert resp.json()["applied_count"] == 1

        db.refresh(t)
        assert t.id_category == category_transport.id  # high priority wins

    def test_apply_regex_anchored(self, client, auth_headers, db, category_food, account_checking, currency_eur):
        rule = TagRule(
            name="Anchored regex",
            id_category=category_food.id,
            match_description="^colruyt",
            priority=10,
            is_active=True,
        )
        db.add(rule)
        db.flush()

        t_match = Transaction(
            external_id="regex-1",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("10.00"),
            id_currency=currency_eur.id,
            description="Colruyt Brussels",
            is_reviewed=False,
        )
        t_no_match = Transaction(
            external_id="regex-2",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("10.00"),
            id_currency=currency_eur.id,
            description="Payment to Colruyt",
            is_reviewed=False,
        )
        db.add_all([t_match, t_no_match])
        db.flush()

        resp = client.post("/api/v2/tag-rules/apply", headers=auth_headers)
        assert resp.json()["applied_count"] == 1

        db.refresh(t_match)
        db.refresh(t_no_match)
        assert t_match.id_category == category_food.id
        assert t_no_match.id_category is None

    def test_apply_plain_string_backward_compat(
        self, client, auth_headers, db, tag_rule, account_checking, currency_eur
    ):
        """Plain string pattern still matches as substring (backward compat)."""
        t = Transaction(
            external_id="compat-1",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("10.00"),
            id_currency=currency_eur.id,
            description="Payment to Colruyt supermarket",
            is_reviewed=False,
        )
        db.add(t)
        db.flush()

        resp = client.post("/api/v2/tag-rules/apply", headers=auth_headers)
        assert resp.json()["applied_count"] == 1

        db.refresh(t)
        assert t.id_category == tag_rule.id_category
