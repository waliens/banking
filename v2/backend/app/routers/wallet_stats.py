import datetime
from collections import defaultdict
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


def _get_category_descendants(db: Session, id_category: int) -> list[int]:
    """BFS over Category table to find all descendants of a category (inclusive)."""
    result = [id_category]
    queue = [id_category]
    while queue:
        parent_id = queue.pop(0)
        children = db.execute(
            select(Category.id).where(Category.id_parent == parent_id)
        ).scalars().all()
        for child_id in children:
            result.append(child_id)
            queue.append(child_id)
    return result


def _get_category_level_mapping(db: Session, level: int) -> dict[int, int]:
    """Map each category id to its ancestor at the target depth.

    Level 0 = root categories (no parent), level 1 = their children, etc.
    If a category is shallower than the target level, it maps to itself.
    """
    all_cats = db.execute(select(Category.id, Category.id_parent)).all()
    parent_map: dict[int, int | None] = {c.id: c.id_parent for c in all_cats}

    def get_depth(cat_id: int) -> int:
        depth = 0
        current = cat_id
        while parent_map.get(current) is not None:
            current = parent_map[current]
            depth += 1
        return depth

    def get_ancestor_at_level(cat_id: int) -> int:
        depth = get_depth(cat_id)
        if depth <= level:
            return cat_id
        # Walk up (depth - level) steps
        current = cat_id
        for _ in range(depth - level):
            current = parent_map[current]
        return current

    return {cat_id: get_ancestor_at_level(cat_id) for cat_id in parent_map}


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
    level: int | None = None,
    id_category: int | None = None,
    period_bucket: str | None = None,
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

    # Filter by category descendants
    if id_category is not None:
        descendant_ids = _get_category_descendants(db, id_category)
        filters.append(Transaction.id_category.in_(descendant_ids))

    # Build SELECT columns and GROUP BY
    select_cols = [
        Transaction.id_category,
        Category.name.label("category_name"),
        Category.color.label("category_color"),
        Category.icon.label("category_icon"),
        Category.id_parent.label("id_parent"),
        func.sum(effective).label("amount"),
        Transaction.id_currency,
    ]
    group_cols = [
        Transaction.id_category,
        Category.name,
        Category.color,
        Category.icon,
        Category.id_parent,
        Transaction.id_currency,
    ]

    if period_bucket in ("month", "year"):
        select_cols.append(extract("year", Transaction.date).label("period_year"))
        group_cols.append(extract("year", Transaction.date))
        if period_bucket == "month":
            select_cols.append(extract("month", Transaction.date).label("period_month"))
            group_cols.append(extract("month", Transaction.date))

    q = (
        select(*select_cols)
        .outerjoin(Category, Transaction.id_category == Category.id)
        .where(*filters)
        .group_by(*group_cols)
        .order_by(func.sum(effective).desc())
    )

    rows = db.execute(q).all()

    # Build raw items
    raw_items = []
    for row in rows:
        item = CategoryStatItem(
            id_category=row.id_category,
            category_name=row.category_name,
            category_color=row.category_color,
            category_icon=getattr(row, "category_icon", None),
            id_parent=getattr(row, "id_parent", None),
            amount=row.amount,
            id_currency=row.id_currency,
            period_year=int(row.period_year) if hasattr(row, "period_year") and row.period_year is not None else None,
            period_month=int(row.period_month) if hasattr(row, "period_month") and row.period_month is not None else None,
        )
        raw_items.append(item)

    # Level aggregation: remap categories to ancestors at target depth
    if level is not None:
        level_map = _get_category_level_mapping(db, level)

        # Load ancestor info
        ancestor_ids = set(level_map.values())
        ancestors = {}
        if ancestor_ids:
            ancestor_rows = db.execute(
                select(Category.id, Category.name, Category.color, Category.icon, Category.id_parent)
                .where(Category.id.in_(ancestor_ids))
            ).all()
            for a in ancestor_rows:
                ancestors[a.id] = a

        # Aggregate amounts by (ancestor_id, currency, period)
        buckets: dict[tuple, Decimal] = defaultdict(Decimal)
        for item in raw_items:
            if item.id_category is not None:
                ancestor_id = level_map.get(item.id_category, item.id_category)
            else:
                ancestor_id = None
            key = (ancestor_id, item.id_currency, item.period_year, item.period_month)
            buckets[key] += item.amount

        aggregated = []
        for (cat_id, id_currency, p_year, p_month), total_amount in buckets.items():
            if cat_id is not None and cat_id in ancestors:
                a = ancestors[cat_id]
                aggregated.append(CategoryStatItem(
                    id_category=cat_id,
                    category_name=a.name,
                    category_color=a.color,
                    category_icon=a.icon,
                    id_parent=a.id_parent,
                    amount=total_amount,
                    id_currency=id_currency,
                    period_year=p_year,
                    period_month=p_month,
                ))
            else:
                aggregated.append(CategoryStatItem(
                    id_category=cat_id,
                    category_name=None,
                    category_color=None,
                    amount=total_amount,
                    id_currency=id_currency,
                    period_year=p_year,
                    period_month=p_month,
                ))

        # Sort by amount descending
        aggregated.sort(key=lambda x: x.amount, reverse=True)
        return CategoryStatsResponse(items=aggregated)

    return CategoryStatsResponse(items=raw_items)
