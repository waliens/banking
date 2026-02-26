"""Tests for bank file parsers."""

import os
from datetime import date
from decimal import Decimal

import pytest

from app.parsers import belfius, ing
from app.parsers.common import sanitize, sanitize_number, parse_date_str

from app.models import ImportRecord, Transaction

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestCommonUtils:
    def test_sanitize_strips_whitespace(self):
        assert sanitize("  hello world  ") == "hello world"

    def test_sanitize_collapses_spaces(self):
        assert sanitize("hello   world") == "hello world"

    def test_sanitize_empty_returns_none(self):
        assert sanitize("   ") is None
        assert sanitize("") is None

    def test_sanitize_number_removes_spaces(self):
        assert sanitize_number("BE12 3456 7890") == "BE1234567890"

    def test_sanitize_number_empty_returns_none(self):
        assert sanitize_number("  ") is None

    def test_parse_date_slash_format(self):
        assert parse_date_str("01/06/2024") == date(2024, 6, 1)

    def test_parse_date_dash_format(self):
        assert parse_date_str("01-06-2024") == date(2024, 6, 1)

    def test_parse_date_two_digit_year(self):
        assert parse_date_str("01/06/24") == date(2024, 6, 1)


class TestBelfiusParser:
    def test_parse_file(self):
        filepath = os.path.join(FIXTURES_DIR, "belfius_sample.csv")
        transactions = belfius.parse_file(filepath)

        assert len(transactions) == 2

        # first transaction: expense (-50.00)
        t1 = transactions[0]
        assert t1.amount == Decimal("50.00")
        assert t1.date == date(2024, 6, 1)
        assert t1.currency == "EUR"
        assert t1.data_source == "belfius"
        # negative amount means source=my account, dest=other
        assert t1.source_number == "BE12345678901234"
        assert t1.dest_name == "John Doe"
        assert t1.description == "Monthly payment"

        # second transaction: income (100.00)
        t2 = transactions[1]
        assert t2.amount == Decimal("100.00")
        assert t2.date == date(2024, 6, 15)
        # positive amount means source=other, dest=my account
        assert t2.source_name == "Jane Smith"

    def test_external_id_is_unique(self):
        filepath = os.path.join(FIXTURES_DIR, "belfius_sample.csv")
        transactions = belfius.parse_file(filepath)
        ids = [t.external_id for t in transactions]
        assert len(ids) == len(set(ids))

    def test_external_id_contains_ref(self):
        filepath = os.path.join(FIXTURES_DIR, "belfius_sample.csv")
        transactions = belfius.parse_file(filepath)
        assert "ABC123" in transactions[0].external_id

    def test_metadata_fields(self):
        filepath = os.path.join(FIXTURES_DIR, "belfius_sample.csv")
        transactions = belfius.parse_file(filepath)
        meta = transactions[0].raw_metadata
        assert "valued_at" in meta
        assert "statement_nb" in meta
        assert "transaction_nb" in meta
        assert "bic" in meta
        assert "country_code" in meta


class TestIngParser:
    def test_parse_file(self):
        filepath = os.path.join(FIXTURES_DIR, "ing_sample.csv")
        transactions = ing.parse_file(filepath)

        # should skip the zero-amount transaction (row 3)
        assert len(transactions) == 2

        # first transaction: expense (-25.50)
        t1 = transactions[0]
        assert t1.amount == Decimal("25.50")
        assert t1.date == date(2024, 6, 1)
        assert t1.currency == "EUR"
        assert t1.data_source == "ing"
        assert t1.description == "Achat supermarche"

        # second transaction: income (1250.00)
        t2 = transactions[1]
        assert t2.amount == Decimal("1250.00")
        assert t2.date == date(2024, 6, 15)

    def test_skips_zero_amount(self):
        filepath = os.path.join(FIXTURES_DIR, "ing_sample.csv")
        transactions = ing.parse_file(filepath)
        amounts = [t.amount for t in transactions]
        assert Decimal("0") not in amounts

    def test_external_id_is_unique(self):
        filepath = os.path.join(FIXTURES_DIR, "ing_sample.csv")
        transactions = ing.parse_file(filepath)
        ids = [t.external_id for t in transactions]
        assert len(ids) == len(set(ids))

    def test_metadata_fields(self):
        filepath = os.path.join(FIXTURES_DIR, "ing_sample.csv")
        transactions = ing.parse_file(filepath)
        meta = transactions[0].raw_metadata
        assert "valued_at" in meta
        assert "transaction_nb" in meta
        assert "communication" in meta

    def test_large_amount_with_dot_separator(self):
        """ING uses dots for thousands (1.250,00 = 1250.00)."""
        filepath = os.path.join(FIXTURES_DIR, "ing_sample.csv")
        transactions = ing.parse_file(filepath)
        t2 = transactions[1]
        assert t2.amount == Decimal("1250.00")


class TestImportService:
    """Integration tests for the import service with the test DB."""

    def test_import_parsed_transactions(self, db, currency_eur):
        from app.parsers.common import ParsedTransaction
        from app.services.import_service import import_parsed_transactions

        parsed = [
            ParsedTransaction(
                external_id="import-test-1",
                source_number=None,
                source_name="Shop A",
                dest_number="BE1234",
                dest_name=None,
                date=date(2024, 3, 15),
                amount=Decimal("42.50"),
                currency="EUR",
                description="Groceries",
                data_source="belfius",
            ),
            ParsedTransaction(
                external_id="import-test-2",
                source_number=None,
                source_name="Shop B",
                dest_number="BE1234",
                dest_name=None,
                date=date(2024, 3, 16),
                amount=Decimal("15.00"),
                currency="EUR",
                description="Coffee",
                data_source="belfius",
            ),
        ]

        import_record = import_parsed_transactions(db, parsed, "belfius")
        assert import_record.new_transactions == 2

        transactions = (
            db.query(Transaction)
            .filter_by(id_import=import_record.id)
            .order_by(Transaction.id)
            .all()
        )
        assert len(transactions) == 2
        assert transactions[0].description == "Groceries"
        assert transactions[1].description == "Coffee"

    def test_import_skips_already_imported(self, db, currency_eur, sample_transaction):
        from app.parsers.common import ParsedTransaction
        from app.services.import_service import import_parsed_transactions

        parsed = [
            ParsedTransaction(
                external_id=sample_transaction.external_id,  # already exists
                source_number=None,
                source_name=None,
                dest_number=None,
                dest_name=None,
                date=date(2024, 6, 15),
                amount=Decimal("50.00"),
                currency="EUR",
                description="Duplicate",
                data_source="manual",
            ),
        ]

        import_record = import_parsed_transactions(db, parsed, "manual")
        assert import_record.new_transactions == 0
