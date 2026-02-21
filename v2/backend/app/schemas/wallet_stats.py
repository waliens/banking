from decimal import Decimal

from pydantic import BaseModel


class AccountBalanceItem(BaseModel):
    id: int
    name: str | None
    number: str | None
    balance: Decimal
    id_currency: int
    currency_symbol: str


class WalletBalanceResponse(BaseModel):
    accounts: list[AccountBalanceItem]


class IncomeExpenseItem(BaseModel):
    year: int
    month: int
    income: Decimal
    expense: Decimal
    id_currency: int


class IncomeExpenseResponse(BaseModel):
    items: list[IncomeExpenseItem]


class CategoryStatItem(BaseModel):
    id_category: int | None
    category_name: str | None
    category_color: str | None
    amount: Decimal
    id_currency: int


class CategoryStatsResponse(BaseModel):
    items: list[CategoryStatItem]
