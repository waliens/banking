from decimal import Decimal

from pydantic import BaseModel

from app.schemas.transaction import TransactionResponse


class TransactionGroupResponse(BaseModel):
    id: int
    name: str | None
    transactions: list[TransactionResponse] = []
    total_paid: Decimal
    total_reimbursed: Decimal
    net_expense: Decimal

    model_config = {"from_attributes": True}


class TransactionGroupCreate(BaseModel):
    name: str | None = None
    transaction_ids: list[int]


class TransactionGroupUpdate(BaseModel):
    name: str | None = None
    transaction_ids: list[int] | None = None
