from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Account, AccountAlias, MLModel, Transaction, User
from app.schemas.account import (
    AccountAliasCreate,
    AccountAliasResponse,
    AccountCountResponse,
    AccountMerge,
    AccountResponse,
    AccountUpdate,
)

router = APIRouter()


class MergeSuggestion(BaseModel):
    account_a: AccountResponse
    account_b: AccountResponse
    score: float
    reason: str


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    start: int = 0,
    count: int | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[Account]:
    q = select(Account)
    if search:
        term = f"%{search}%"
        q = q.where(or_(
            Account.name.ilike(term),
            Account.number.ilike(term),
        ))
    q = q.order_by(Account.name, Account.number, Account.id).offset(start)
    if count is not None:
        q = q.limit(count)
    return list(db.execute(q).scalars().unique().all())


@router.get("/merge-suggestions", response_model=list[MergeSuggestion])
def merge_suggestions(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[MergeSuggestion]:
    accounts = list(db.execute(select(Account)).scalars().unique().all())

    # Build set of already-aliased pairs to exclude
    aliased_ids: set[int] = set()
    for a in accounts:
        for alias in a.aliases:
            aliased_ids.add(a.id)

    suggestions: list[MergeSuggestion] = []

    for i, a in enumerate(accounts):
        for b in accounts[i + 1 :]:
            score = 0.0
            reason = ""

            # Name similarity
            if a.name and b.name:
                name_sim = SequenceMatcher(None, a.name.lower(), b.name.lower()).ratio()
                if name_sim > 0.7:
                    score = max(score, name_sim)
                    reason = "similar_name"

            # IBAN prefix matching (first 8 chars = same bank)
            if a.number and b.number:
                if a.number[:8] == b.number[:8] and len(a.number) >= 8 and len(b.number) >= 8:
                    iban_score = 0.6
                    if a.name and b.name and a.name.lower() == b.name.lower():
                        iban_score = 0.95
                        reason = "same_name_different_number"
                    score = max(score, iban_score)
                    if not reason:
                        reason = "same_bank"

            # Same number different name
            if a.number and b.number and a.number == b.number:
                score = max(score, 0.9)
                reason = "same_number"

            if score >= 0.6:
                suggestions.append(
                    MergeSuggestion(
                        account_a=AccountResponse.model_validate(a),
                        account_b=AccountResponse.model_validate(b),
                        score=round(score, 3),
                        reason=reason,
                    )
                )

    # Sort by score descending, limit to 20
    suggestions.sort(key=lambda s: s.score, reverse=True)
    return suggestions[:20]


@router.get("/count", response_model=AccountCountResponse)
def count_accounts(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> AccountCountResponse:
    total = db.execute(select(func.count()).select_from(Account)).scalar_one()
    return AccountCountResponse(count=total)


@router.put("/merge", response_model=AccountResponse)
def merge_accounts(
    body: AccountMerge, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> Account:
    if body.id_alias == body.id_repr:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot merge an account with itself")

    alias_acc = db.get(Account, body.id_alias)
    repr_acc = db.get(Account, body.id_repr)
    if alias_acc is None or repr_acc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    # check no transactions between the two
    between = (
        db.query(Transaction)
        .filter(
            or_(
                (Transaction.id_source == repr_acc.id) & (Transaction.id_dest == alias_acc.id),
                (Transaction.id_source == alias_acc.id) & (Transaction.id_dest == repr_acc.id),
            )
        )
        .count()
    )
    if between > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot merge accounts that have transactions between them",
        )

    # move aliases
    db.execute(update(AccountAlias).where(AccountAlias.id_account == alias_acc.id).values(id_account=repr_acc.id))

    # move transaction references
    db.execute(update(Transaction).where(Transaction.id_source == alias_acc.id).values(id_source=repr_acc.id))
    db.execute(update(Transaction).where(Transaction.id_dest == alias_acc.id).values(id_dest=repr_acc.id))

    # add old account as alias then delete
    db.add(AccountAlias(name=alias_acc.name, number=alias_acc.number, id_account=repr_acc.id))
    db.delete(alias_acc)

    # invalidate ML models
    db.execute(update(MLModel).where(MLModel.state != "deleted").values(state="invalid"))

    db.commit()
    db.refresh(repr_acc)
    return repr_acc


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> Account:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int, body: AccountUpdate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> Account:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(account, key, value)

    db.commit()
    db.refresh(account)
    return account


@router.post("/{account_id}/aliases", response_model=AccountAliasResponse, status_code=status.HTTP_201_CREATED)
def add_alias(
    account_id: int, body: AccountAliasCreate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> AccountAlias:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    # check if alias already exists
    all_names = [(account.name, account.number)] + [(a.name, a.number) for a in account.aliases]
    if (body.name, body.number) in all_names:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alias already exists")

    alias = AccountAlias(name=body.name, number=body.number, id_account=account_id)
    db.add(alias)
    db.commit()
    db.refresh(alias)
    return alias


@router.delete("/{account_id}/aliases/{alias_id}", status_code=status.HTTP_200_OK)
def remove_alias(
    account_id: int,
    alias_id: int,
    promote: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, str]:
    alias = db.get(AccountAlias, alias_id)
    if alias is None or alias.id_account != account_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alias not found")

    if promote:
        # Promote alias to a standalone account
        account = db.get(Account, account_id)
        new_account = Account(
            name=alias.name,
            number=alias.number,
            initial_balance=0,
            id_currency=account.id_currency if account else 1,
            institution=account.institution if account else None,
            is_active=True,
        )
        db.add(new_account)
        db.delete(alias)
        db.commit()
        return {"msg": "alias promoted to account"}

    db.delete(alias)
    db.commit()
    return {"msg": "alias removed"}
