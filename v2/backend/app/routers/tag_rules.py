"""Tag rules CRUD + apply endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import TagRule, Transaction, User
from app.schemas.tag_rule import TagRuleApplyResponse, TagRuleCreate, TagRuleResponse, TagRuleUpdate
from app.services.tag_rule_service import apply_rules

router = APIRouter()


@router.get("", response_model=list[TagRuleResponse])
def list_tag_rules(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list[TagRule]:
    return db.query(TagRule).order_by(TagRule.priority.desc()).all()


@router.post("", response_model=TagRuleResponse, status_code=status.HTTP_201_CREATED)
def create_tag_rule(
    body: TagRuleCreate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> TagRule:
    rule = TagRule(**body.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/{rule_id}", response_model=TagRuleResponse)
def get_tag_rule(rule_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> TagRule:
    rule = db.get(TagRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag rule not found")
    return rule


@router.put("/{rule_id}", response_model=TagRuleResponse)
def update_tag_rule(
    rule_id: int, body: TagRuleUpdate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> TagRule:
    rule = db.get(TagRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag rule not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag_rule(rule_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> None:
    rule = db.get(TagRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag rule not found")
    db.delete(rule)
    db.commit()


@router.post("/apply", response_model=TagRuleApplyResponse)
def apply_tag_rules(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> TagRuleApplyResponse:
    uncategorized = (
        db.query(Transaction)
        .filter(~Transaction.category_splits.any(), Transaction.id_duplicate_of.is_(None))
        .all()
    )
    count = apply_rules(db, uncategorized)
    return TagRuleApplyResponse(applied_count=count)
