from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Transaction, TransactionGroup, User
from app.schemas.transaction_group import (
    TransactionGroupCreate,
    TransactionGroupResponse,
    TransactionGroupUpdate,
)

router = APIRouter()


def _classify_transactions(transactions: list) -> tuple[list, list]:
    """Classify transactions as outgoing or incoming.

    The largest transaction is assumed to be a payment (outgoing).
    Its id_source identifies the owner account. Transactions with
    the same id_source are outgoing; others are incoming.
    """
    if not transactions:
        return [], []
    ref_tx = max(transactions, key=lambda t: t.amount)
    owner_account = ref_tx.id_source
    outgoing = [t for t in transactions if t.id_source == owner_account]
    incoming = [t for t in transactions if t.id_source != owner_account]
    return outgoing, incoming


def _recompute_effective_amounts(db: Session, group: TransactionGroup) -> None:
    """Auto-compute effective_amount for all transactions in the group.

    Outgoing transactions get proportionally reduced.
    Incoming transactions get effective_amount = 0.
    """
    transactions = group.transactions
    if not transactions:
        return

    outgoing, incoming = _classify_transactions(transactions)

    total_paid = sum(t.amount for t in outgoing)
    total_reimbursed = sum(t.amount for t in incoming)

    if total_paid > 0:
        ratio = total_reimbursed / total_paid
    else:
        ratio = Decimal(0)

    for t in outgoing:
        t.effective_amount = (t.amount * (1 - ratio)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    for t in incoming:
        t.effective_amount = Decimal(0)

    db.flush()


def _build_response(group: TransactionGroup) -> TransactionGroupResponse:
    transactions = group.transactions or []
    outgoing, incoming = _classify_transactions(transactions)

    total_paid = sum(t.amount for t in outgoing) if outgoing else Decimal(0)
    total_reimbursed = sum(t.amount for t in incoming) if incoming else Decimal(0)

    return TransactionGroupResponse(
        id=group.id,
        name=group.name,
        transactions=transactions,
        total_paid=total_paid,
        total_reimbursed=total_reimbursed,
        net_expense=total_paid - total_reimbursed,
    )


def _load_and_validate_transactions(db: Session, transaction_ids: list[int]) -> list[Transaction]:
    if not transaction_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one transaction ID is required")

    transactions = db.execute(
        select(Transaction).where(Transaction.id.in_(transaction_ids))
    ).scalars().unique().all()

    found_ids = {t.id for t in transactions}
    missing = set(transaction_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transactions not found: {sorted(missing)}",
        )
    return list(transactions)


@router.get("", response_model=list[TransactionGroupResponse])
def list_groups(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[TransactionGroupResponse]:
    groups = db.execute(select(TransactionGroup)).scalars().unique().all()
    return [_build_response(g) for g in groups]


@router.get("/{group_id}", response_model=TransactionGroupResponse)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TransactionGroupResponse:
    group = db.get(TransactionGroup, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction group not found")
    return _build_response(group)


@router.post("", response_model=TransactionGroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    body: TransactionGroupCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TransactionGroupResponse:
    transactions = _load_and_validate_transactions(db, body.transaction_ids)

    group = TransactionGroup(name=body.name)
    db.add(group)
    db.flush()

    for t in transactions:
        t.id_transaction_group = group.id
    db.flush()

    # Reload to populate relationship
    db.refresh(group)
    _recompute_effective_amounts(db, group)
    db.commit()
    db.refresh(group)

    return _build_response(group)


@router.put("/{group_id}", response_model=TransactionGroupResponse)
def update_group(
    group_id: int,
    body: TransactionGroupUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TransactionGroupResponse:
    group = db.get(TransactionGroup, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction group not found")

    if body.name is not None:
        group.name = body.name

    if body.transaction_ids is not None:
        new_transactions = _load_and_validate_transactions(db, body.transaction_ids)

        # Unlink old transactions
        for t in group.transactions:
            t.id_transaction_group = None
            t.effective_amount = None
        db.flush()

        # Link new transactions
        for t in new_transactions:
            t.id_transaction_group = group.id
        db.flush()

        db.refresh(group)
        _recompute_effective_amounts(db, group)

    db.commit()
    db.refresh(group)
    return _build_response(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> None:
    group = db.get(TransactionGroup, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction group not found")

    # Reset effective_amount on all member transactions
    for t in group.transactions:
        t.id_transaction_group = None
        t.effective_amount = None

    db.delete(group)
    db.commit()
