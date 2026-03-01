import datetime
import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Select, exists, func, or_, select, update
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.dependencies import get_current_user, get_db
from app.models import Category, CategorySplit, Transaction, User, WalletAccount
from app.schemas.ml import PredictionItem
from app.schemas.transaction import (
    EffectiveAmountUpdate,
    ReviewBatchRequest,
    ReviewBatchResponse,
    ReviewInboxCountResponse,
    SetCategorySplitsRequest,
    TransactionCountResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionTagBatch,
    TransactionUpdate,
)

router = APIRouter()


def _get_category_descendants(db: Session, id_category: int) -> list[int]:
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


def _build_transaction_query(
    db: Session,
    *,
    account: int | None = None,
    account_from: int | None = None,
    account_to: int | None = None,
    wallet: int | None = None,
    wallet_external_only: bool = False,
    labeled: bool | None = None,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    amount_from: Decimal | None = None,
    amount_to: Decimal | None = None,
    duplicate_only: bool = False,
    is_reviewed: bool | None = None,
    search_query: str | None = None,
    sort_by: str | None = None,
    order: str = "desc",
    import_id: int | None = None,
    exclude_grouped: bool = False,
    category: int | None = None,
) -> Select[tuple[Transaction]]:
    q = select(Transaction)

    if account is not None:
        q = q.where(or_(Transaction.id_source == account, Transaction.id_dest == account))
    if account_from is not None:
        q = q.where(Transaction.id_source == account_from)
    if account_to is not None:
        q = q.where(Transaction.id_dest == account_to)

    if wallet is not None:
        wallet_account_ids = select(WalletAccount.id_account).where(WalletAccount.id_wallet == wallet)
        if wallet_external_only:
            # at least one side outside the wallet
            q = q.where(
                or_(
                    Transaction.id_source.in_(wallet_account_ids),
                    Transaction.id_dest.in_(wallet_account_ids),
                )
            ).where(
                or_(
                    Transaction.id_source.not_in(wallet_account_ids),
                    Transaction.id_dest.not_in(wallet_account_ids),
                    Transaction.id_source.is_(None),
                    Transaction.id_dest.is_(None),
                )
            )
        else:
            q = q.where(
                or_(
                    Transaction.id_source.in_(wallet_account_ids),
                    Transaction.id_dest.in_(wallet_account_ids),
                )
            )

    if labeled is True:
        q = q.where(Transaction.category_splits.any())
    elif labeled is False:
        q = q.where(~Transaction.category_splits.any())

    if is_reviewed is not None:
        q = q.where(Transaction.is_reviewed == is_reviewed)

    if date_from is not None:
        q = q.where(Transaction.date >= date_from)
    if date_to is not None:
        q = q.where(Transaction.date <= date_to)

    if amount_from is not None:
        q = q.where(Transaction.amount >= amount_from)
    if amount_to is not None:
        q = q.where(Transaction.amount <= amount_to)

    if duplicate_only:
        q = q.where(Transaction.id_duplicate_of.is_not(None))
    else:
        q = q.where(Transaction.id_duplicate_of.is_(None))

    if import_id is not None:
        q = q.where(Transaction.id_import == import_id)

    if exclude_grouped:
        q = q.where(Transaction.id_transaction_group.is_(None))

    if category is not None:
        descendant_ids = _get_category_descendants(db, category)
        q = q.join(CategorySplit, CategorySplit.id_transaction == Transaction.id).where(
            CategorySplit.id_category.in_(descendant_ids)
        )

    if search_query and len(search_query) >= 3:
        q = q.where(Transaction.description.ilike(f"%{search_query}%"))

    # sorting
    sort_col: InstrumentedAttribute[Any] = Transaction.date
    if sort_by == "amount":
        sort_col = Transaction.amount

    if order == "asc":
        q = q.order_by(sort_col.asc(), Transaction.id.asc())
    else:
        q = q.order_by(sort_col.desc(), Transaction.id.desc())

    return q


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    start: int = 0,
    count: int = 50,
    order: str = "desc",
    sort_by: str | None = None,
    account: int | None = None,
    account_from: int | None = None,
    account_to: int | None = None,
    wallet: int | None = None,
    wallet_external_only: bool = False,
    labeled: bool | None = None,
    is_reviewed: bool | None = None,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    amount_from: Decimal | None = None,
    amount_to: Decimal | None = None,
    duplicate_only: bool = False,
    search_query: str | None = None,
    import_id: int | None = None,
    exclude_grouped: bool = False,
    category: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[Transaction]:
    q = _build_transaction_query(
        db,
        account=account,
        account_from=account_from,
        account_to=account_to,
        wallet=wallet,
        wallet_external_only=wallet_external_only,
        labeled=labeled,
        is_reviewed=is_reviewed,
        date_from=date_from,
        date_to=date_to,
        amount_from=amount_from,
        amount_to=amount_to,
        duplicate_only=duplicate_only,
        search_query=search_query,
        sort_by=sort_by,
        order=order,
        import_id=import_id,
        exclude_grouped=exclude_grouped,
        category=category,
    )
    results = db.execute(q.offset(start).limit(count)).scalars().unique().all()
    return list(results)


@router.get("/count", response_model=TransactionCountResponse)
def count_transactions(
    account: int | None = None,
    account_from: int | None = None,
    account_to: int | None = None,
    wallet: int | None = None,
    wallet_external_only: bool = False,
    labeled: bool | None = None,
    is_reviewed: bool | None = None,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    amount_from: Decimal | None = None,
    amount_to: Decimal | None = None,
    duplicate_only: bool = False,
    search_query: str | None = None,
    import_id: int | None = None,
    exclude_grouped: bool = False,
    category: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TransactionCountResponse:
    q = _build_transaction_query(
        db,
        account=account,
        account_from=account_from,
        account_to=account_to,
        wallet=wallet,
        wallet_external_only=wallet_external_only,
        labeled=labeled,
        is_reviewed=is_reviewed,
        date_from=date_from,
        date_to=date_to,
        amount_from=amount_from,
        amount_to=amount_to,
        duplicate_only=duplicate_only,
        search_query=search_query,
        import_id=import_id,
        exclude_grouped=exclude_grouped,
        category=category,
    )
    count_q = select(func.count()).select_from(q.subquery())
    return TransactionCountResponse(count=db.execute(count_q).scalar_one())


@router.put("/tag", status_code=status.HTTP_200_OK)
def tag_batch(
    body: TransactionTagBatch, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> dict[str, str]:
    for item in body.categories:
        tx_id = item["id_transaction"]
        cat_id = item["id_category"]
        t = db.get(Transaction, tx_id)
        if t is None:
            continue
        # Delete existing splits and create a single new one
        for cs in list(t.category_splits):
            db.delete(cs)
        db.flush()
        effective = t.effective_amount if t.effective_amount is not None else t.amount
        t.category_splits.append(CategorySplit(id_category=cat_id, amount=effective))
        t.is_reviewed = True
    db.commit()
    return {"msg": "success"}


@router.put("/review-batch", response_model=ReviewBatchResponse)
def review_batch(
    body: ReviewBatchRequest, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> ReviewBatchResponse:
    db.execute(update(Transaction).where(Transaction.id.in_(body.transaction_ids)).values(is_reviewed=True))
    db.commit()
    return ReviewBatchResponse(msg="success", count=len(body.transaction_ids))


@router.get("/review-inbox/count", response_model=ReviewInboxCountResponse)
def review_inbox_count(
    db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> ReviewInboxCountResponse:
    has_split = exists(select(CategorySplit.id).where(CategorySplit.id_transaction == Transaction.id))
    q = select(func.count()).select_from(
        select(Transaction)
        .where(
            Transaction.is_reviewed == False,  # noqa: E712
            ~has_split,
            Transaction.id_duplicate_of.is_(None),
        )
        .subquery()
    )
    count = db.execute(q).scalar_one()
    return ReviewInboxCountResponse(count=count)


@router.put("/{transaction_id}/review", response_model=TransactionResponse)
def review_transaction(
    transaction_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> Transaction:
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    t.is_reviewed = True
    db.commit()
    db.refresh(t)
    return t


@router.put("/{transaction_id}/effective-amount", response_model=TransactionResponse)
def set_effective_amount(
    transaction_id: int,
    body: EffectiveAmountUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Transaction:
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    t.effective_amount = body.effective_amount
    # Rescale single split if present
    if len(t.category_splits) == 1:
        new_amount = body.effective_amount if body.effective_amount is not None else t.amount
        t.category_splits[0].amount = new_amount
    db.commit()
    db.refresh(t)
    return t


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> Transaction:
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return t


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    body: TransactionCreate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> Transaction:
    amount = body.amount
    id_source, id_dest = body.id_source, body.id_dest
    if amount < 0:
        id_source, id_dest = id_dest, id_source
        amount = abs(amount)

    t = Transaction(
        external_id=str(uuid.uuid4()),
        id_source=id_source,
        id_dest=id_dest,
        date=body.date,
        raw_metadata=body.raw_metadata or {},
        amount=amount,
        id_currency=body.id_currency,
        data_source="manual",
        description=body.description,
        notes=body.notes,
        is_reviewed=body.id_category is not None,
    )
    db.add(t)
    db.flush()

    if body.id_category is not None:
        t.category_splits.append(CategorySplit(id_category=body.id_category, amount=amount))

    db.commit()
    db.refresh(t)
    return t


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int, body: TransactionUpdate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> Transaction:
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if t.data_source != "manual":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a non-manual transaction")

    update_data = body.model_dump(exclude_unset=True)

    # handle amount sign flip
    if "amount" in update_data and update_data["amount"] is not None:
        amount = update_data["amount"]
        if amount < 0:
            update_data["amount"] = abs(amount)
            update_data.setdefault("id_source", t.id_dest)
            update_data.setdefault("id_dest", t.id_source)

    for key, value in update_data.items():
        setattr(t, key, value)

    db.commit()
    db.refresh(t)
    return t


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> None:
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if t.data_source != "manual":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a non-manual transaction")

    db.delete(t)
    db.commit()


@router.put("/{transaction_id}/category/{category_id}", response_model=TransactionResponse)
def set_category(
    transaction_id: int, category_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> Transaction:
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    # Delete existing splits and create a single new one
    for cs in list(t.category_splits):
        db.delete(cs)
    db.flush()
    effective = t.effective_amount if t.effective_amount is not None else t.amount
    t.category_splits.append(CategorySplit(id_category=category_id, amount=effective))
    t.is_reviewed = True
    db.commit()
    db.refresh(t)
    return t


@router.put("/{transaction_id}/category-splits", response_model=TransactionResponse)
def set_category_splits(
    transaction_id: int,
    body: SetCategorySplitsRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Transaction:
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if t.id_transaction_group is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction is in a group; set splits on the group instead")
    if len(body.splits) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least 2 splits required")

    expected = t.effective_amount if t.effective_amount is not None else t.amount
    total = sum(s.amount for s in body.splits)
    if total != expected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Split total {total} does not match expected {expected}",
        )

    for cs in list(t.category_splits):
        db.delete(cs)
    db.flush()
    for s in body.splits:
        t.category_splits.append(CategorySplit(id_category=s.id_category, amount=s.amount))
    t.is_reviewed = True
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{transaction_id}/category-splits", response_model=TransactionResponse)
def clear_category_splits(
    transaction_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Transaction:
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    for cs in list(t.category_splits):
        db.delete(cs)
    db.commit()
    db.refresh(t)
    return t


@router.get("/{transaction_id}/duplicate_candidates", response_model=list[TransactionResponse])
def get_duplicate_candidates(
    transaction_id: int,
    days: int = 7,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[Transaction]:
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    after_date = t.date - datetime.timedelta(days=days)
    before_date = t.date + datetime.timedelta(days=days)

    filters = [
        Transaction.amount == t.amount,
        Transaction.date > after_date,
        Transaction.date < before_date,
        Transaction.id != t.id,
        Transaction.id_duplicate_of.is_(None),
    ]
    if t.id_source is not None:
        filters.append(or_(Transaction.id_source.is_(None), Transaction.id_source == t.id_source))
    if t.id_dest is not None:
        filters.append(or_(Transaction.id_dest.is_(None), Transaction.id_dest == t.id_dest))

    candidates = db.execute(select(Transaction).where(*filters)).scalars().unique().all()
    return list(candidates)


@router.put("/{id_duplicate}/duplicate_of/{id_parent}")
def set_duplicate(
    id_duplicate: int, id_parent: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> dict[str, str]:
    parent = db.get(Transaction, id_parent)
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent transaction not found")
    if parent.id_duplicate_of is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent is already a duplicate")

    duplicate = db.get(Transaction, id_duplicate)
    if duplicate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duplicate transaction not found")

    duplicate.id_duplicate_of = id_parent
    db.commit()
    return {"msg": "success"}


@router.delete("/{transaction_id}/duplicate_of")
def unset_duplicate(
    transaction_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> dict[str, str]:
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    t.id_duplicate_of = None
    db.commit()
    return {"msg": "success"}


@router.get("/{transaction_id}/predict", response_model=PredictionItem)
def predict_single(
    transaction_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> PredictionItem:
    from app.ml.predictor import InferenceError, NoValidModelError, predict_category
    from app.models import Category

    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    try:
        cat_id, prob = predict_category(db, t)
    except NoValidModelError:
        return PredictionItem(
            transaction_id=t.id, category_id=None, category_name=None, category_color=None, probability=0.0
        )
    except InferenceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    cat = db.get(Category, cat_id) if cat_id is not None else None
    # If predicted category no longer exists (stale model), return null
    return PredictionItem(
        transaction_id=t.id,
        category_id=cat.id if cat else None,
        category_name=cat.name if cat else None,
        category_color=cat.color if cat else None,
        probability=round(prob, 4) if cat else 0.0,
    )
