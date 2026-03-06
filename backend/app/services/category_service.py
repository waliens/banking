"""Category-related service functions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category


def get_category_descendants(db: Session, id_category: int) -> list[int]:
    """BFS over Category table to find all descendants of a category (inclusive)."""
    result = [id_category]
    queue = [id_category]
    while queue:
        parent_id = queue.pop(0)
        children = db.execute(
            select(Category.id).where(Category.id_parent == parent_id)
        ).scalars().all()
        for child_id in children:
            result.append(child_id)
            queue.append(child_id)
    return result
