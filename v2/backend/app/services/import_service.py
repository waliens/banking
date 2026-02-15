"""Import service: handles file parsing, account resolution, duplicate detection, and transaction creation."""

import bisect
import datetime
import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, AccountAlias, Currency, Transaction
from app.parsers.common import ParsedTransaction

logger = logging.getLogger(__name__)


def resolve_account(db: Session, number: str | None, name: str | None, id_currency: int) -> Account | None:
    """Find or create an account by number/name."""
    if number is None and name is None:
        return None

    # try by number first
    if number is not None:
        account = db.query(Account).filter(Account.number == number).first()
        if account:
            return account
        # try aliases
        alias = db.query(AccountAlias).filter(AccountAlias.number == number).first()
        if alias:
            return db.get(Account, alias.id_account)

    # try by name
    if name is not None:
        account = db.query(Account).filter(Account.name == name).first()
        if account:
            return account
        alias = db.query(AccountAlias).filter(AccountAlias.name == name).first()
        if alias:
            return db.get(Account, alias.id_account)

    # create new account
    account = Account(number=number, name=name, initial_balance=0, id_currency=id_currency)
    db.add(account)
    db.flush()
    return account


def find_duplicates(db: Session, transactions: list[Transaction]) -> dict[str | None, int | None]:
    """Find duplicate transactions. Returns mapping of external_id -> id of the original."""

    def key_fn(t: Transaction) -> tuple[int, int, datetime.date, Decimal]:
        return (t.id_source or -1, t.id_dest or -1, t.date, t.amount)

    remaining = list(transactions)
    checked: list[Transaction] = []
    duplicate_map: dict[str | None, int | None] = {}

    while remaining:
        t = remaining.pop()
        results = (
            db.execute(
                select(Transaction).where(
                    Transaction.id_source == t.id_source,
                    Transaction.id_dest == t.id_dest,
                    Transaction.date == t.date,
                    Transaction.amount == t.amount,
                    Transaction.id_duplicate_of.is_(None),
                )
            )
            .scalars()
            .unique()
            .all()
        )

        if results:
            duplicate_map[t.external_id] = results[0].id
        else:
            idx = bisect.bisect_left(checked, key_fn(t), key=key_fn)
            if idx < len(checked) and key_fn(checked[idx]) == key_fn(t):
                duplicate_map[t.external_id] = None  # dup within batch, will resolve after flush
            else:
                checked.insert(idx, t)

    return duplicate_map


def import_parsed_transactions(
    db: Session,
    parsed: list[ParsedTransaction],
    data_source: str,
) -> list[Transaction]:
    """Import parsed transactions into the database.

    Resolves accounts, detects duplicates, creates transactions.
    """
    currencies = {c.short_name: c for c in db.query(Currency).all()}
    existing_ids = {row[0] for row in db.execute(select(Transaction.external_id)).all()}

    # filter already imported
    new_parsed = [p for p in parsed if p.external_id not in existing_ids]
    if not new_parsed:
        return []

    default_currency_id = currencies.get("EUR", next(iter(currencies.values()))).id

    # resolve accounts and build Transaction objects
    transactions = []
    for p in new_parsed:
        currency = currencies.get(p.currency)
        currency_id = currency.id if currency else default_currency_id

        source = resolve_account(db, p.source_number, p.source_name, currency_id)
        dest = resolve_account(db, p.dest_number, p.dest_name, currency_id)

        t = Transaction(
            external_id=p.external_id,
            id_source=source.id if source else None,
            id_dest=dest.id if dest else None,
            date=p.date,
            raw_metadata=p.raw_metadata,
            amount=p.amount,
            id_currency=currency_id,
            id_category=None,
            data_source=data_source,
            description=p.description,
            is_reviewed=False,
        )
        transactions.append(t)

    # detect duplicates
    duplicate_map = find_duplicates(db, transactions)

    # save all
    db.add_all(transactions)
    db.flush()

    # set duplicate references
    for t in transactions:
        if t.external_id in duplicate_map:
            parent_id = duplicate_map[t.external_id]
            if parent_id is not None:
                t.id_duplicate_of = parent_id

    db.commit()

    logger.info("Imported %d new transaction(s) (%d duplicates)", len(transactions), len(duplicate_map))
    return transactions
