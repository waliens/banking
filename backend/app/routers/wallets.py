from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User, Wallet, WalletAccount
from app.schemas.wallet import WalletCreate, WalletResponse, WalletUpdate

router = APIRouter()


@router.get("", response_model=list[WalletResponse])
def list_wallets(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list[Wallet]:
    return db.query(Wallet).all()


@router.get("/{wallet_id}", response_model=WalletResponse)
def get_wallet(wallet_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> Wallet:
    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return wallet


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def create_wallet(body: WalletCreate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> Wallet:
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty wallet name")
    if not body.accounts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must include at least one account")

    wallet = Wallet(name=name, description=body.description)
    db.add(wallet)
    db.flush()

    for wa in body.accounts:
        if not (0 < wa.contribution_ratio <= 1):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid contribution ratio")
        db.add(WalletAccount(id_wallet=wallet.id, id_account=wa.id_account, contribution_ratio=wa.contribution_ratio))

    db.commit()
    db.refresh(wallet)
    return wallet


@router.put("/{wallet_id}", response_model=WalletResponse)
def update_wallet(
    wallet_id: int, body: WalletUpdate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> Wallet:
    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    if body.name is not None:
        wallet.name = body.name.strip()
    if body.description is not None:
        wallet.description = body.description.strip()

    if body.accounts is not None:
        db.execute(delete(WalletAccount).where(WalletAccount.id_wallet == wallet_id))
        for wa in body.accounts:
            db.add(
                WalletAccount(id_wallet=wallet_id, id_account=wa.id_account, contribution_ratio=wa.contribution_ratio)
            )

    db.commit()
    db.refresh(wallet)
    return wallet


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wallet(wallet_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> None:
    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    db.delete(wallet)
    db.commit()
