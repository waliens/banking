"""Tests for category_service.get_category_descendants."""

import pytest

from app.models import Category
from app.services.category_service import get_category_descendants


class TestGetCategoryDescendants:
    def test_leaf_category_returns_only_itself(self, db, category_food):
        """A leaf category (no children) should return just its own ID."""
        result = get_category_descendants(db, category_food.id)
        assert result == [category_food.id]

    def test_parent_returns_parent_and_children(self, db, category_food, category_child):
        """A parent category should return itself plus all direct children."""
        result = get_category_descendants(db, category_food.id)
        assert set(result) == {category_food.id, category_child.id}
        # Parent should come first (BFS order)
        assert result[0] == category_food.id

    def test_deeply_nested_categories(self, db, category_food, category_child):
        """Should return all descendants at any depth."""
        # Add a grandchild under category_child (Groceries)
        grandchild = Category(
            name="Organic", color="#FF7777",
            id_parent=category_child.id, sort_order=0, is_income=False,
        )
        db.add(grandchild)
        db.flush()

        # Add a great-grandchild
        great_grandchild = Category(
            name="Organic Fruit", color="#FF9999",
            id_parent=grandchild.id, sort_order=0, is_income=False,
        )
        db.add(great_grandchild)
        db.flush()

        result = get_category_descendants(db, category_food.id)
        assert set(result) == {
            category_food.id,
            category_child.id,
            grandchild.id,
            great_grandchild.id,
        }
        # BFS order: root, child, grandchild, great-grandchild
        assert result[0] == category_food.id
        assert result[1] == category_child.id
        assert result[2] == grandchild.id
        assert result[3] == great_grandchild.id

    def test_nonexistent_category_returns_id_only(self, db):
        """A non-existent category ID should return a list with just that ID.

        The function does not validate existence; it simply starts BFS from
        the given ID and finds no children, so it returns [id].
        """
        result = get_category_descendants(db, 999999)
        assert result == [999999]

    def test_multiple_children(self, db, category_food):
        """A parent with multiple direct children returns all of them."""
        child_a = Category(
            name="Restaurants", color="#FF1111",
            id_parent=category_food.id, sort_order=0, is_income=False,
        )
        child_b = Category(
            name="Takeout", color="#FF2222",
            id_parent=category_food.id, sort_order=1, is_income=False,
        )
        db.add_all([child_a, child_b])
        db.flush()

        result = get_category_descendants(db, category_food.id)
        assert set(result) == {category_food.id, child_a.id, child_b.id}
        assert result[0] == category_food.id

    def test_sibling_subtrees_not_included(self, db, category_food, category_salary):
        """Descendants of one root should not include another root's subtree."""
        # Add a child under salary
        salary_child = Category(
            name="Bonus", color="#00CC00",
            id_parent=category_salary.id, sort_order=0, is_income=True,
        )
        db.add(salary_child)
        db.flush()

        result = get_category_descendants(db, category_food.id)
        assert salary_child.id not in result
        assert category_salary.id not in result
        assert result == [category_food.id]
