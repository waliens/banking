import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.account import AccountResponse, CurrencyResponse
from app.schemas.category import CategoryResponse


class TransactionResponse(BaseModel):
    id: int
    external_id: str | None
    id_source: int | None
    id_dest: int | None
    date: datetime.date
    raw_metadata: dict[str, object] | None
    amount: Decimal
    id_currency: int
    id_category: int | None
    data_source: str | None
    id_duplicate_of: int | None
    description: str
    is_reviewed: bool
    notes: str | None
    effective_amount: Decimal | None
    id_transaction_group: int | None
    id_import: int | None = None
    source: AccountResponse | None = None
    dest: AccountResponse | None = None
    currency: CurrencyResponse
    category: CategoryResponse | None = None

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    id_source: int | None = None
    id_dest: int | None = None
    date: datetime.date
    raw_metadata: dict[str, object] | None = None
    amount: Decimal
    id_currency: int
    id_category: int | None = None
    description: str = ""
    notes: str | None = None


class TransactionUpdate(BaseModel):
    id_source: int | None = None
    id_dest: int | None = None
    date: datetime.date | None = None
    raw_metadata: dict[str, object] | None = None
    amount: Decimal | None = None
    id_currency: int | None = None
    id_category: int | None = None
    description: str | None = None
    notes: str | None = None
    is_reviewed: bool | None = None
    effective_amount: Decimal | None = None


class TransactionTagBatch(BaseModel):
    categories: list[dict[str, int]]


class TransactionCountResponse(BaseModel):
    count: int


class ReviewBatchRequest(BaseModel):
    transaction_ids: list[int]


class ReviewBatchResponse(BaseModel):
    msg: str
    count: int


class EffectiveAmountUpdate(BaseModel):
    effective_amount: Decimal | None


class ReviewInboxCountResponse(BaseModel):
    count: int
