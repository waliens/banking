from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import CategorySplit, Transaction, TransactionGroup, User, Wallet, WalletAccount
from app.schemas.transaction import CategorySplitResponse, SetCategorySplitsRequest
from app.schemas.transaction_group import (
    TransactionGroupCreate,
    TransactionGroupResponse,
    TransactionGroupUpdate,
)

router = APIRouter()


def _get_wallet_account_ids(db: Session, wallet_id: int) -> set[int]:
    """Get account IDs for a wallet, raising 404 if wallet not found."""
    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    rows = db.execute(
        select(WalletAccount.id_account).where(WalletAccount.id_wallet == wallet_id)
    ).scalars().all()
    return set(rows)


def _classify_transactions(transactions: list, wallet_account_ids: set[int]) -> tuple[list, list]:
    """Classify transactions as outgoing or incoming based on wallet accounts.

    Outgoing = source account is in the wallet.
    Incoming = source account is NOT in the wallet.
    """
    if not transactions:
        return [], []
    outgoing = [t for t in transactions if t.id_source in wallet_account_ids]
    incoming = [t for t in transactions if t.id_source not in wallet_account_ids]
    return outgoing, incoming


def _recompute_effective_amounts(db: Session, group: TransactionGroup, wallet_account_ids: set[int]) -> None:
    """Auto-compute effective_amount for all transactions in the group.

    Outgoing transactions get proportionally reduced.
    Incoming transactions get effective_amount = 0.
    """
    transactions = group.transactions
    if not transactions:
        return

    outgoing, incoming = _classify_transactions(transactions, wallet_account_ids)

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


def _build_response(group: TransactionGroup, wallet_account_ids: set[int]) -> TransactionGroupResponse:
    transactions = group.transactions or []
    outgoing, incoming = _classify_transactions(transactions, wallet_account_ids)

    total_paid = sum(t.amount for t in outgoing) if outgoing else Decimal(0)
    total_reimbursed = sum(t.amount for t in incoming) if incoming else Decimal(0)

    return TransactionGroupResponse(
        id=group.id,
        name=group.name,
        transactions=transactions,
        total_paid=total_paid,
        total_reimbursed=total_reimbursed,
        net_expense=total_paid - total_reimbursed,
        category_splits=group.category_splits,
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


def _clear_transaction_splits(db: Session, transactions: list[Transaction]) -> None:
    """Clear individual category splits from transactions being added to a group."""
    for t in transactions:
        for cs in list(t.category_splits):
            db.delete(cs)


@router.get("", response_model=list[TransactionGroupResponse])
def list_groups(
    wallet_id: int = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[TransactionGroupResponse]:
    wallet_account_ids = _get_wallet_account_ids(db, wallet_id)
    groups = db.execute(select(TransactionGroup)).scalars().unique().all()
    return [_build_response(g, wallet_account_ids) for g in groups]


@router.get("/{group_id}", response_model=TransactionGroupResponse)
def get_group(
    group_id: int,
    wallet_id: int = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TransactionGroupResponse:
    wallet_account_ids = _get_wallet_account_ids(db, wallet_id)
    group = db.get(TransactionGroup, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction group not found")
    return _build_response(group, wallet_account_ids)


@router.post("", response_model=TransactionGroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    body: TransactionGroupCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TransactionGroupResponse:
    wallet_account_ids = _get_wallet_account_ids(db, body.wallet_id)
    transactions = _load_and_validate_transactions(db, body.transaction_ids)

    # Check that no transaction is already in another group
    already_grouped = [t for t in transactions if t.id_transaction_group is not None]
    if already_grouped:
        ids = sorted(t.id for t in already_grouped)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transactions already in a group: {ids}",
        )

    # Clear individual splits from transactions being added to the group
    _clear_transaction_splits(db, transactions)

    group = TransactionGroup(name=body.name)
    db.add(group)
    db.flush()

    for t in transactions:
        t.id_transaction_group = group.id
    db.flush()

    # Reload to populate relationship
    db.refresh(group)
    _recompute_effective_amounts(db, group, wallet_account_ids)
    db.commit()
    db.refresh(group)

    return _build_response(group, wallet_account_ids)


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

    # wallet_id is required when updating transactions
    if body.transaction_ids is not None and body.wallet_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="wallet_id is required when updating transactions",
        )

    if body.name is not None:
        group.name = body.name

    if body.transaction_ids is not None:
        wallet_account_ids = _get_wallet_account_ids(db, body.wallet_id)
        new_transactions = _load_and_validate_transactions(db, body.transaction_ids)

        # Check that no transaction is already in a different group
        already_grouped = [
            t for t in new_transactions
            if t.id_transaction_group is not None and t.id_transaction_group != group_id
        ]
        if already_grouped:
            ids = sorted(t.id for t in already_grouped)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transactions already in a group: {ids}",
            )

        # Unlink old transactions
        for t in group.transactions:
            t.id_transaction_group = None
            t.effective_amount = None
        db.flush()

        # Clear individual splits from new transactions being added
        _clear_transaction_splits(db, new_transactions)

        # Link new transactions
        for t in new_transactions:
            t.id_transaction_group = group.id
        db.flush()

        db.refresh(group)
        _recompute_effective_amounts(db, group, wallet_account_ids)

    db.commit()
    db.refresh(group)

    # For response building, use wallet_id from body if provided, otherwise use empty set
    if body.wallet_id is not None:
        wallet_account_ids = _get_wallet_account_ids(db, body.wallet_id)
    else:
        wallet_account_ids = set()

    return _build_response(group, wallet_account_ids)


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


@router.put("/{group_id}/category-splits", response_model=TransactionGroupResponse)
def set_group_category_splits(
    group_id: int,
    body: SetCategorySplitsRequest,
    wallet_id: int = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TransactionGroupResponse:
    wallet_account_ids = _get_wallet_account_ids(db, wallet_id)
    group = db.get(TransactionGroup, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction group not found")
    if len(body.splits) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least 2 splits required")

    response = _build_response(group, wallet_account_ids)
    expected = response.net_expense
    total = sum(s.amount for s in body.splits)
    if total != expected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Split total {total} does not match net_expense {expected}",
        )

    for cs in list(group.category_splits):
        db.delete(cs)
    db.flush()
    for s in body.splits:
        group.category_splits.append(CategorySplit(id_category=s.id_category, amount=s.amount))
    db.commit()
    db.refresh(group)
    return _build_response(group, wallet_account_ids)


@router.delete("/{group_id}/category-splits", response_model=TransactionGroupResponse)
def clear_group_category_splits(
    group_id: int,
    wallet_id: int = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TransactionGroupResponse:
    wallet_account_ids = _get_wallet_account_ids(db, wallet_id)
    group = db.get(TransactionGroup, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction group not found")
    for cs in list(group.category_splits):
        db.delete(cs)
    db.commit()
    db.refresh(group)
    return _build_response(group, wallet_account_ids)
