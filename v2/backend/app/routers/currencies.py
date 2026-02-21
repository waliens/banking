from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Currency, User
from app.schemas.account import CurrencyResponse

router = APIRouter()


@router.get("", response_model=list[CurrencyResponse])
def list_currencies(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list[Currency]:
    return db.query(Currency).all()
