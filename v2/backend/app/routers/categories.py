import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Category, CategorySplit, MLModel, User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter()


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list[Category]:
    return db.query(Category).order_by(Category.sort_order, Category.name).all()


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    body: CategoryCreate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> Category:
    if re.match(r"^#[A-Fa-f0-9]{6}$", body.color) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid color '{body.color}'")
    if len(body.name) < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty category name")

    category = Category(**body.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, body: CategoryUpdate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    # invalidate ML models when category changes
    db.execute(update(MLModel).where(MLModel.state != "deleted").values(state="invalid"))

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> None:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # reparent children
    db.execute(update(Category).where(Category.id_parent == category_id).values(id_parent=category.id_parent))
    # delete split rows referencing this category (CASCADE handles it but be explicit)
    db.execute(delete(CategorySplit).where(CategorySplit.id_category == category_id))
    # delete
    db.execute(delete(Category).where(Category.id == category_id))
    # invalidate ML models
    db.execute(update(MLModel).where(MLModel.state != "deleted").values(state="invalid"))

    db.commit()
