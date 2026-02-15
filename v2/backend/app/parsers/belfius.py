import os
import re
from datetime import date
from decimal import Decimal

from app.parsers.common import ParsedTransaction, parse_csv_file, parse_date_str, sanitize, sanitize_number


def _account_tag(number: str | None) -> str:
    if number is not None:
        return number.replace(" ", "")
    return ""


def _extract_ref(transaction: str) -> str:
    match = re.match(r".*REF\. : ([0-9A-Za-z]+)( .*)?$", transaction)
    return match.group(1) if match else "noref"


def _make_external_id(t: ParsedTransaction, valued_at: date, transaction_field: str) -> str:
    ref = _extract_ref(transaction_field or "")
    return f"{t.date.isoformat()}/{valued_at.isoformat()}/{_account_tag(t.source_number)}/{_account_tag(t.dest_number)}/{t.amount:.2f}/{ref}"


def check_files(path: str) -> bool:
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        if filename.rsplit(".", 1)[-1] in {"pdf", "json", "db"}:
            continue
        rows = parse_csv_file(filepath, header_length=12)
        for row in rows:
            if row[0] != "Compte":
                return False
            break
    return True


def parse_file(filepath: str) -> list[ParsedTransaction]:
    transactions = []

    for row in parse_csv_file(filepath):
        my_account_number = sanitize_number(row[0])
        other_acc_nb = sanitize_number(row[4])
        other_acc_name = sanitize(row[5])

        amount = Decimal(row[10].replace(",", "."))
        valued_at = parse_date_str(row[9]).isoformat()
        when = parse_date_str(row[1])

        src_number, src_name = my_account_number, None
        dest_number, dest_name = other_acc_nb, other_acc_name
        if amount > 0:
            src_number, src_name = other_acc_nb, other_acc_name
            dest_number, dest_name = my_account_number, None

        transaction_field = sanitize(row[8])
        communication = sanitize(row[14])

        t = ParsedTransaction(
            external_id="",  # set below
            source_number=src_number,
            source_name=src_name,
            dest_number=dest_number,
            dest_name=dest_name,
            date=when,
            amount=amount.copy_abs(),
            currency=row[11].strip(),
            description=communication or transaction_field or "",
            data_source="belfius",
            raw_metadata={
                "valued_at": valued_at,
                "statement_nb": sanitize(row[2]),
                "transaction_nb": sanitize(row[3]),
                "road_number": sanitize(row[6]),
                "postal_code_city": sanitize(row[7]),
                "transaction": transaction_field,
                "bic": sanitize(row[12]),
                "country_code": sanitize(row[13]),
                "communication": communication,
            },
        )
        t.external_id = _make_external_id(t, parse_date_str(row[9]), transaction_field or "")
        transactions.append(t)

    return transactions


def parse_folder(path: str) -> list[ParsedTransaction]:
    all_transactions = []
    for filename in os.listdir(path):
        if filename.rsplit(".", 1)[-1] in {"pdf", "json", "db"}:
            continue
        filepath = os.path.join(path, filename)
        all_transactions.extend(parse_file(filepath))
    return all_transactions
