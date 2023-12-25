import csv
import json
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, Iterable, Set

from parsing.data_parser import BankParserOrchestrator
from parsing import Account, Transaction, AccountBook
from parsing.transaction import Currency


def sanitize(e):
    """strip and replace multiple consecutive spaces by single space"""
    cleaned = re.sub("\s+", " ", e.strip())
    return None if len(cleaned) == 0 else cleaned


def parse_belfius_csv_file(filepath, encoding="latin1", header_length=13, skip_header=True):
    with open(filepath, "r", encoding=encoding) as file:
        reader = csv.reader(file, delimiter=";")
        for i, row in enumerate(reader):
            if skip_header and i < header_length:
                continue
            yield row


def parse_date(s):
    return datetime.strptime(sanitize(s), "%d/%m/%Y")


def account_tag(a: Account):
    s = ""
    if a.number is not None:
        s += a.number.replace(" ", "")
    return s


def extract_ref(transaction: str):
    match = re.match(r".*REF\. : ([0-9A-Za-z]+)( .*)?$", transaction)
    if match is None:
        return "noref"
    else:
        return match.group(1)


def identifier_fn(t: Transaction):
    return "{when}/{valued}/{_from}/{_to}/{amount}/{ref}".format(
        when=t.when.isoformat(),
        valued=t.metadata["valued_at"].isoformat(),
        _from=account_tag(t.source),
        _to=account_tag(t.dest),
        amount=t.amount,
        ref=extract_ref(t.metadata["transaction"]))



class BelfiusParserOrchestrator(BankParserOrchestrator):
    def get_transaction_files(self, path: str):
        return [
            os.path.join(path, f)
            for f in  os.listdir(path) if "." not in f or f.rsplit(".", 1)[1] not in {'pdf', 'json', 'db'}
        ]

    def read_personal_accounts(self, path: str) -> Dict[str, Iterable[Account]]:
        with open(os.path.join(path, "accounts.json"), "r", encoding="utf-8") as file:
            content = json.load(file)
            groups = dict()
            for name, groups_data in content.items():
                groups[name] = [Account(acc["number"], acc["name"], initial=acc.get("initial", "0.0")) for acc in groups_data]
            return groups 

    def read_accounts(self, path: str) -> Set:
        accounts = set()
        for filepath in self.get_transaction_files(path):
            for i, row in enumerate(parse_belfius_csv_file(filepath)):
                if i == 0:
                    accounts.add((sanitize(row[0]), None))
                accounts.add(Account(sanitize(row[4]), sanitize(row[5])).identifier)
        return accounts

    def read_transactions_file(self, filepath: str, account_book: AccountBook) -> Iterable[Transaction]:
        """Update account db as well"""
        transactions = list()
        number = None

        for i, row in enumerate(parse_belfius_csv_file(filepath)):
            """
            Column ids:
            -  0: my_account
            -  1: accounted_at
            -  2: statement_nb
            -  3: transaction_nb
            -  4: other_account
            -  5: other_name
            -  6: road_number
            -  7: postal_code_city
            -  8: transaction
            -  9: valued_at
            - 10: amount
            - 11: currency
            - 12: bic
            - 13: country_code
            - 14: communication
            """

            my_account = account_book.get_by_number(sanitize(row[0]))
            number = my_account.number
            other_acc_nb = sanitize(row[4])
            other_acc_name = sanitize(row[5])
            other_account = account_book[Account(other_acc_nb, other_acc_name).identifier]

            amount = Decimal(row[10].replace(",", "."))

            src_account, dest_account = my_account, other_account
            if amount > 0:
                src_account, dest_account = dest_account, src_account

            t = Transaction(
                amount=amount.copy_abs(),
                src=src_account, dest=dest_account,
                currency=Currency.validate(row[11]),
                when=parse_date(row[1]).date(),
                id_fn=identifier_fn,
                valued_at=parse_date(row[9]).date(),
                statement_nb=sanitize(row[2]),
                transaction_nb=sanitize(row[3]),
                road_number=sanitize(row[6]),
                postal_code_city=sanitize(row[7]),
                transaction=sanitize(row[8]),
                bic=sanitize(row[12]),
                country_code=sanitize(row[13]),
                communication=sanitize(row[14])
            )

            transactions.append(t)

        return number, transactions