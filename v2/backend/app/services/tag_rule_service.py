"""Tag rule matching service for auto-categorizing transactions."""

import re

from sqlalchemy.orm import Session

from app.models.tag_rule import TagRule
from app.models.transaction import Transaction


def apply_rules(db: Session, transactions: list[Transaction]) -> int:
    """Apply active tag rules to uncategorized transactions.

    Rules are checked in priority order (highest first). First match wins.
    Returns the number of transactions that were categorized.
    """
    rules = db.query(TagRule).filter(TagRule.is_active == True).order_by(TagRule.priority.desc()).all()  # noqa: E712
    if not rules:
        return 0

    applied = 0
    for t in transactions:
        if t.id_category is not None:
            continue
        for rule in rules:
            if _matches(rule, t):
                t.id_category = rule.id_category
                t.is_reviewed = True
                applied += 1
                break

    if applied > 0:
        db.commit()

    return applied


def _matches(rule: TagRule, transaction: Transaction) -> bool:
    """Check if a transaction matches all conditions of a rule."""
    if rule.match_description is not None:
        try:
            if not re.search(rule.match_description, transaction.description, re.IGNORECASE):
                return False
        except re.error:
            return False
    if rule.match_amount_min is not None:
        if transaction.amount < rule.match_amount_min:
            return False
    if rule.match_amount_max is not None:
        if transaction.amount > rule.match_amount_max:
            return False
    if rule.match_account_from is not None:
        if transaction.id_source != rule.match_account_from:
            return False
    if rule.match_account_to is not None:
        if transaction.id_dest != rule.match_account_to:
            return False
    return True
