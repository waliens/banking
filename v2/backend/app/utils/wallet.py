from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Wallet, WalletAccount


def get_wallet_or_404(db: Session, wallet_id: int) -> Wallet:
    """Fetch a wallet by ID or raise HTTP 404."""
    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return wallet


def get_wallet_account_ids(db: Session, wallet_id: int) -> set[int]:
    """Get account IDs for a wallet, raising 404 if wallet not found."""
    get_wallet_or_404(db, wallet_id)
    rows = db.execute(
        select(WalletAccount.id_account).where(WalletAccount.id_wallet == wallet_id)
    ).scalars().all()
    return set(rows)
