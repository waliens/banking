from decimal import Decimal

from pydantic import BaseModel


class CurrencyResponse(BaseModel):
    id: int
    symbol: str
    short_name: str
    long_name: str

    model_config = {"from_attributes": True}


class AccountAliasResponse(BaseModel):
    id: int
    number: str | None
    name: str | None
    id_account: int

    model_config = {"from_attributes": True}


class AccountResponse(BaseModel):
    id: int
    number: str | None
    name: str | None
    initial_balance: Decimal
    id_currency: int
    institution: str | None
    is_active: bool
    currency: CurrencyResponse
    aliases: list[AccountAliasResponse] = []

    model_config = {"from_attributes": True}


class AccountUpdate(BaseModel):
    initial_balance: Decimal | None = None
    institution: str | None = None
    is_active: bool | None = None


class AccountAliasCreate(BaseModel):
    name: str | None = None
    number: str | None = None


class AccountMerge(BaseModel):
    id_alias: int
    id_repr: int
