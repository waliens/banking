import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select, case, extract, func, or_, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Account, Category, Currency, Transaction, User, Wallet, WalletAccount
from app.schemas.wallet_stats import (
    AccountBalanceItem,
    CategoryStatItem,
    CategoryStatsResponse,
    IncomeExpenseItem,
    IncomeExpenseResponse,
    WalletBalanceResponse,
)

router = APIRouter()

effective = func.coalesce(Transaction.effective_amount, Transaction.amount)


def _get_wallet_or_404(db: Session, wallet_id: int) -> Wallet:
    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return wallet


def _wallet_account_ids(wallet_id: int) -> Select[tuple[int]]:
    return select(WalletAccount.id_account).where(WalletAccount.id_wallet == wallet_id)


@router.get("/{wallet_id}/stats/balance", response_model=WalletBalanceResponse)
def wallet_balance(
    wallet_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> WalletBalanceResponse:
    _get_wallet_or_404(db, wallet_id)

    acct_ids_sq = _wallet_account_ids(wallet_id)

    # Sum incoming amounts per account (where account is dest)
    incoming = (
        select(
            Transaction.id_dest.label("account_id"),
            func.coalesce(func.sum(effective), Decimal(0)).label("total"),
        )
        .where(Transaction.id_dest.in_(acct_ids_sq), Transaction.id_duplicate_of.is_(None))
        .group_by(Transaction.id_dest)
        .subquery()
    )

    # Sum outgoing amounts per account (where account is source)
    outgoing = (
        select(
            Transaction.id_source.label("account_id"),
            func.coalesce(func.sum(effective), Decimal(0)).label("total"),
        )
        .where(Transaction.id_source.in_(acct_ids_sq), Transaction.id_duplicate_of.is_(None))
        .group_by(Transaction.id_source)
        .subquery()
    )

    q = (
        select(
            Account.id,
            Account.name,
            Account.number,
            Account.initial_balance,
            Account.id_currency,
            Currency.symbol.label("currency_symbol"),
            func.coalesce(incoming.c.total, Decimal(0)).label("incoming_total"),
            func.coalesce(outgoing.c.total, Decimal(0)).label("outgoing_total"),
        )
        .join(Currency, Account.id_currency == Currency.id)
        .outerjoin(incoming, Account.id == incoming.c.account_id)
        .outerjoin(outgoing, Account.id == outgoing.c.account_id)
        .where(Account.id.in_(acct_ids_sq))
    )

    rows = db.execute(q).all()
    accounts = [
        AccountBalanceItem(
            id=row.id,
            name=row.name,
            number=row.number,
            balance=row.initial_balance + row.incoming_total - row.outgoing_total,
            id_currency=row.id_currency,
            currency_symbol=row.currency_symbol,
        )
        for row in rows
    ]
    return WalletBalanceResponse(accounts=accounts)


@router.get("/{wallet_id}/stats/income-expense", response_model=IncomeExpenseResponse)
def wallet_income_expense(
    wallet_id: int,
    year: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> IncomeExpenseResponse:
    wallet = _get_wallet_or_404(db, wallet_id)

    acct_ids_sq = _wallet_account_ids(wallet_id)

    # External-only transactions: at least one side in wallet, at least one side outside
    base_filter = [
        Transaction.id_duplicate_of.is_(None),
        or_(
            Transaction.id_source.in_(acct_ids_sq),
            Transaction.id_dest.in_(acct_ids_sq),
        ),
        or_(
            Transaction.id_source.not_in(acct_ids_sq),
            Transaction.id_dest.not_in(acct_ids_sq),
            Transaction.id_source.is_(None),
            Transaction.id_dest.is_(None),
        ),
    ]

    if year is not None:
        base_filter.append(extract("year", Transaction.date) == year)

    # Income: dest is in wallet (money coming in from outside)
    income_case = case(
        (Transaction.id_dest.in_(acct_ids_sq), effective),
        else_=Decimal(0),
    )
    # Expense: source is in wallet (money going out)
    expense_case = case(
        (Transaction.id_source.in_(acct_ids_sq), effective),
        else_=Decimal(0),
    )

    q = (
        select(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            func.sum(income_case).label("income"),
            func.sum(expense_case).label("expense"),
            Transaction.id_currency,
        )
        .where(*base_filter)
        .group_by(
            extract("year", Transaction.date),
            extract("month", Transaction.date),
            Transaction.id_currency,
        )
        .order_by(
            extract("year", Transaction.date),
            extract("month", Transaction.date),
        )
    )

    rows = db.execute(q).all()
    items = [
        IncomeExpenseItem(
            year=int(row.year),
            month=int(row.month),
            income=row.income or Decimal(0),
            expense=row.expense or Decimal(0),
            id_currency=row.id_currency,
        )
        for row in rows
    ]
    return IncomeExpenseResponse(items=items)


@router.get("/{wallet_id}/stats/per-category", response_model=CategoryStatsResponse)
def wallet_per_category(
    wallet_id: int,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    income_only: bool = False,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> CategoryStatsResponse:
    wallet = _get_wallet_or_404(db, wallet_id)

    acct_ids_sq = _wallet_account_ids(wallet_id)

    # External-only
    filters = [
        Transaction.id_duplicate_of.is_(None),
        or_(
            Transaction.id_source.in_(acct_ids_sq),
            Transaction.id_dest.in_(acct_ids_sq),
        ),
        or_(
            Transaction.id_source.not_in(acct_ids_sq),
            Transaction.id_dest.not_in(acct_ids_sq),
            Transaction.id_source.is_(None),
            Transaction.id_dest.is_(None),
        ),
    ]

    if date_from is not None:
        filters.append(Transaction.date >= date_from)
    if date_to is not None:
        filters.append(Transaction.date <= date_to)

    if income_only:
        # Income: dest is in wallet
        filters.append(Transaction.id_dest.in_(acct_ids_sq))
    else:
        # Expense: source is in wallet
        filters.append(Transaction.id_source.in_(acct_ids_sq))

    q = (
        select(
            Transaction.id_category,
            Category.name.label("category_name"),
            Category.color.label("category_color"),
            func.sum(effective).label("amount"),
            Transaction.id_currency,
        )
        .outerjoin(Category, Transaction.id_category == Category.id)
        .where(*filters)
        .group_by(
            Transaction.id_category,
            Category.name,
            Category.color,
            Transaction.id_currency,
        )
        .order_by(func.sum(effective).desc())
    )

    rows = db.execute(q).all()
    items = [
        CategoryStatItem(
            id_category=row.id_category,
            category_name=row.category_name,
            category_color=row.category_color,
            amount=row.amount,
            id_currency=row.id_currency,
        )
        for row in rows
    ]
    return CategoryStatsResponse(items=items)
