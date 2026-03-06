import datetime
from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import Select, case, extract, func, or_, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Account, Category, CategorySplit, Currency, Transaction, TransactionGroup, User, WalletAccount
from app.services.category_service import get_category_descendants
from app.utils.wallet import get_wallet_or_404 as _get_wallet_or_404
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


def _wallet_account_ids(wallet_id: int) -> Select[tuple[int]]:
    return select(WalletAccount.id_account).where(WalletAccount.id_wallet == wallet_id)



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
    wallet_acct_set = set(db.execute(acct_ids_sq).scalars().all())

    # Base filters: non-duplicate, external-only
    base_filters = [
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
        base_filters.append(Transaction.date >= date_from)
    if date_to is not None:
        base_filters.append(Transaction.date <= date_to)

    # Direction filter
    direction_filter = []
    if income_only:
        direction_filter.append(Transaction.id_dest.in_(acct_ids_sq))
    else:
        direction_filter.append(Transaction.id_source.in_(acct_ids_sq))

    # Category descendant filter (for individual transactions only; groups handled separately)
    descendant_ids = None
    if id_category is not None:
        descendant_ids = get_category_descendants(db, id_category)

    # ===== Part 1: Individual (non-grouped) transactions =====
    individual_filters = [
        *base_filters,
        *direction_filter,
        Transaction.id_transaction_group.is_(None),
    ]
    if descendant_ids is not None:
        individual_filters.append(CategorySplit.id_category.in_(descendant_ids))

    split_amount = func.coalesce(CategorySplit.amount, effective)
    select_cols = [
        CategorySplit.id_category,
        Category.name.label("category_name"),
        Category.color.label("category_color"),
        Category.icon.label("category_icon"),
        Category.id_parent.label("id_parent"),
        func.sum(split_amount).label("amount"),
        Transaction.id_currency,
    ]
    group_cols = [
        CategorySplit.id_category,
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
        .outerjoin(CategorySplit, CategorySplit.id_transaction == Transaction.id)
        .outerjoin(Category, CategorySplit.id_category == Category.id)
        .where(*individual_filters)
        .group_by(*group_cols)
        .order_by(func.sum(split_amount).desc())
    )

    rows = db.execute(q).all()

    raw_items = []
    for row in rows:
        raw_items.append(CategoryStatItem(
            id_category=row.id_category,
            category_name=row.category_name,
            category_color=row.category_color,
            category_icon=getattr(row, "category_icon", None),
            id_parent=getattr(row, "id_parent", None),
            amount=row.amount or Decimal(0),
            id_currency=row.id_currency,
            period_year=int(row.period_year) if hasattr(row, "period_year") and row.period_year is not None else None,
            period_month=int(row.period_month) if hasattr(row, "period_month") and row.period_month is not None else None,
        ))

    # ===== Part 2: Transaction groups =====
    # Find groups that have at least one member transaction matching base filters
    group_q = (
        select(
            Transaction.id_transaction_group,
            func.min(Transaction.date).label("earliest_date"),
            Transaction.id_currency,
        )
        .where(
            Transaction.id_transaction_group.is_not(None),
            *base_filters,
        )
        .group_by(Transaction.id_transaction_group, Transaction.id_currency)
    )
    group_rows = db.execute(group_q).all()

    for grow in group_rows:
        group = db.get(TransactionGroup, grow.id_transaction_group)
        if group is None:
            continue

        # Compute net expense from ALL member transactions
        txs = group.transactions
        total_paid = sum(
            t.amount for t in txs if t.id_source in wallet_acct_set
        )
        total_reimbursed = sum(
            t.amount for t in txs if t.id_source not in wallet_acct_set
        )
        net = total_paid - total_reimbursed

        # Direction check
        if income_only and net >= 0:
            continue  # not income
        if not income_only and net <= 0:
            continue  # not expense

        amount = abs(net)

        # Period assignment: use earliest transaction date
        p_year = None
        p_month = None
        if period_bucket in ("month", "year"):
            p_year = grow.earliest_date.year if grow.earliest_date else None
            if period_bucket == "month":
                p_month = grow.earliest_date.month if grow.earliest_date else None

        if group.category_splits:
            # Filter by category if requested
            splits = group.category_splits
            if descendant_ids is not None:
                splits = [cs for cs in splits if cs.id_category in descendant_ids]

            for cs in splits:
                cat = cs.category
                raw_items.append(CategoryStatItem(
                    id_category=cs.id_category,
                    category_name=cat.name if cat else None,
                    category_color=cat.color if cat else None,
                    category_icon=cat.icon if cat else None,
                    id_parent=cat.id_parent if cat else None,
                    amount=cs.amount,
                    id_currency=grow.id_currency,
                    period_year=p_year,
                    period_month=p_month,
                ))
        else:
            # Uncategorized group — skip if category filter is set
            if descendant_ids is not None:
                continue
            raw_items.append(CategoryStatItem(
                id_category=None,
                category_name=None,
                category_color=None,
                amount=amount,
                id_currency=grow.id_currency,
                period_year=p_year,
                period_month=p_month,
            ))

    # Merge items by (category, currency, period)
    merged: dict[tuple, CategoryStatItem] = {}
    for item in raw_items:
        key = (item.id_category, item.id_currency, item.period_year, item.period_month)
        if key in merged:
            merged[key].amount += item.amount
        else:
            merged[key] = item
    raw_items = list(merged.values())
    raw_items.sort(key=lambda x: x.amount, reverse=True)

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

        aggregated.sort(key=lambda x: x.amount, reverse=True)
        return CategoryStatsResponse(items=aggregated)

    return CategoryStatsResponse(items=raw_items)
