from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Account, AccountAlias, MLModel, Transaction, User
from app.schemas.account import (
    AccountAliasCreate,
    AccountAliasResponse,
    AccountMerge,
    AccountResponse,
    AccountUpdate,
)

router = APIRouter()


@router.get("", response_model=list[AccountResponse])
def list_accounts(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list[Account]:
    return db.query(Account).all()


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
