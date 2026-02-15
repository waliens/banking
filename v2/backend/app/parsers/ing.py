import os
from decimal import Decimal

from app.parsers.common import ParsedTransaction, parse_csv_file, parse_date_str, sanitize, sanitize_number

ING_ENCODING = "utf-8-sig"


def _account_tag(number: str | None) -> str:
    if number is not None:
        return number.replace(" ", "")
    return ""


def _make_external_id(t: ParsedTransaction, valued_at: str, statement_nb: str, transaction_nb: str | None) -> str:
    return f"{t.date.isoformat()}/{valued_at}/{_account_tag(t.source_number)}/{_account_tag(t.dest_number)}/{t.amount}/{statement_nb}-{transaction_nb}"


def check_files(path: str) -> bool:
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        if filename.rsplit(".", 1)[-1] in {"pdf", "json", "db"}:
            continue
        try:
            rows = parse_csv_file(filepath, header_length=0, encoding=ING_ENCODING)
            for row in rows:
                if row[0] != "Numéro de compte":
                    return False
                break
        except UnicodeDecodeError:
            return False
    return True


def parse_file(filepath: str) -> list[ParsedTransaction]:
    transactions = []

    for row in parse_csv_file(filepath, header_length=1, encoding=ING_ENCODING):
        my_account_number = sanitize_number(row[0])
        other_acc_nb = sanitize_number(row[2])

        amount = Decimal(row[6].replace(".", "").replace(",", "."))
        if amount == 0:
            continue

        when = parse_date_str(row[4])
        valued_at = parse_date_str(row[5]).isoformat()

        src_number, src_name = my_account_number, sanitize(row[1])
        dest_number, dest_name = other_acc_nb, None
        if amount > 0:
            src_number, src_name = other_acc_nb, None
            dest_number, dest_name = my_account_number, sanitize(row[1])

        communication = sanitize(row[8])
        details = sanitize(row[9])
        transaction_nb = sanitize(row[3])
        statement_nb = str(when.year)

        t = ParsedTransaction(
            external_id="",
            source_number=src_number,
            source_name=src_name,
            dest_number=dest_number,
            dest_name=dest_name,
            date=when,
            amount=amount.copy_abs(),
            currency=row[7].strip(),
            description=details or communication or "",
            data_source="ing",
            raw_metadata={
                "valued_at": valued_at,
                "transaction_nb": transaction_nb,
                "statement_nb": statement_nb,
                "communication": communication,
                "details": details,
                "message": sanitize(row[10]),
            },
        )
        t.external_id = _make_external_id(t, valued_at, statement_nb, transaction_nb)
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
