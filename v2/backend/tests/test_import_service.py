"""Unit tests for import_service: resolve_account and find_duplicates."""

import datetime
from decimal import Decimal

from app.models import Account, AccountAlias, Transaction
from app.services.import_service import find_duplicates, resolve_account


class TestResolveAccount:
    def test_creates_new_account_when_not_found(self, db, currency_eur):
        account = resolve_account(db, "BE9999", "New Account", currency_eur.id)
        assert account is not None
        assert account.number == "BE9999"
        assert account.name == "New Account"
        assert account.id_currency == currency_eur.id
        # Should be persisted
        assert account.id is not None

    def test_finds_existing_account_by_number(self, db, account_checking):
        account = resolve_account(db, "BE1234", None, account_checking.id_currency)
        assert account is not None
        assert account.id == account_checking.id

    def test_finds_existing_account_by_name(self, db, account_checking):
        account = resolve_account(db, None, "Checking", account_checking.id_currency)
        assert account is not None
        assert account.id == account_checking.id

    def test_returns_none_when_both_number_and_name_are_none(self, db, currency_eur):
        account = resolve_account(db, None, None, currency_eur.id)
        assert account is None

    def test_tracks_new_account_ids(self, db, currency_eur):
        new_ids: set[int] = set()
        account = resolve_account(db, "BE0001", "Brand New", currency_eur.id, _new_account_ids=new_ids)
        assert account is not None
        assert account.id in new_ids

    def test_does_not_track_existing_account(self, db, account_checking):
        new_ids: set[int] = set()
        resolve_account(db, "BE1234", None, account_checking.id_currency, _new_account_ids=new_ids)
        assert len(new_ids) == 0

    def test_finds_account_by_alias_number(self, db, account_checking, currency_eur):
        alias = AccountAlias(number="ALIAS001", name=None, id_account=account_checking.id)
        db.add(alias)
        db.flush()

        account = resolve_account(db, "ALIAS001", None, currency_eur.id)
        assert account is not None
        assert account.id == account_checking.id

    def test_finds_account_by_alias_name(self, db, account_checking, currency_eur):
        alias = AccountAlias(number=None, name="Alias Name", id_account=account_checking.id)
        db.add(alias)
        db.flush()

        account = resolve_account(db, None, "Alias Name", currency_eur.id)
        assert account is not None
        assert account.id == account_checking.id


class TestFindDuplicates:
    def test_returns_matching_transactions(self, db, account_checking, account_savings, currency_eur):
        # Existing transaction in DB
        existing = Transaction(
            external_id="existing-001",
            id_source=account_checking.id,
            id_dest=account_savings.id,
            date=datetime.date(2024, 7, 1),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
            description="Existing",
        )
        db.add(existing)
        db.flush()

        # New transaction that matches
        new_tx = Transaction(
            external_id="new-001",
            id_source=account_checking.id,
            id_dest=account_savings.id,
            date=datetime.date(2024, 7, 1),
            amount=Decimal("100.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
            description="New but duplicate",
        )

        result = find_duplicates(db, [new_tx])
        assert "new-001" in result
        assert result["new-001"] == existing.id

    def test_returns_empty_when_no_matches(self, db, account_checking, account_savings, currency_eur):
        new_tx = Transaction(
            external_id="unique-001",
            id_source=account_checking.id,
            id_dest=account_savings.id,
            date=datetime.date(2024, 8, 1),
            amount=Decimal("200.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
            description="Unique transaction",
        )

        result = find_duplicates(db, [new_tx])
        assert result == {}

    def test_detects_duplicates_within_batch(self, db, account_checking, account_savings, currency_eur):
        tx1 = Transaction(
            external_id="batch-001",
            id_source=account_checking.id,
            id_dest=account_savings.id,
            date=datetime.date(2024, 7, 1),
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
            description="First in batch",
        )
        tx2 = Transaction(
            external_id="batch-002",
            id_source=account_checking.id,
            id_dest=account_savings.id,
            date=datetime.date(2024, 7, 1),
            amount=Decimal("50.00"),
            id_currency=currency_eur.id,
            data_source="belfius",
            description="Second in batch, same key",
        )

        result = find_duplicates(db, [tx1, tx2])
        # One of them should be flagged as a within-batch duplicate
        assert len(result) == 1
        dup_ext_id = list(result.keys())[0]
        assert dup_ext_id in ("batch-001", "batch-002")
        # Within-batch duplicates have None as parent id
        assert result[dup_ext_id] is None
