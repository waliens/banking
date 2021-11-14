import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from account import AccountGroup, Account, AccountBook, is_iban_be, unibanize_be
from data_parser import ParserOrchestrator, check_add_to_env_group
from transaction import Transaction, Currency
from util import UnionFind


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


class BelfiusParserOrchestrator(ParserOrchestrator):
    """Transaction data as csv files per account. Account groups read from json file.
    Possible to specify accounts which have no csv file, in this case, specify them in accounts_no_csv.
    """
    def __init__(self, accounts_no_csv=None):
        self._accounts_no_csv = {} if accounts_no_csv is None else set(accounts_no_csv)

    def read(self, path, add_env_group=False):
        # read accounts from the csv files
        account_book = self.read_account_book(path)

        # read personal accounts and create groups
        groups = self._read_personal_accounts(path)
        my_account_groups = [AccountGroup(
            {a.identifier for a in accounts}, account_book, name=name
        ) for name, accounts in groups.items()]
        env = AccountGroup(set(), account_book, "environment")

        # create custom groups for personal account without csv
        missing_csv_group = AccountGroup({
            a.identifier for g_name, accs in groups.items() for a in accs
            if a.number in self._accounts_no_csv
        }, account_book, "no_csv")

        # extract all accounts involved in groups
        group_accounts = set()
        for g in my_account_groups:
            group_accounts = group_accounts.union({a.identifier for a in g})

        # add transactions
        transaction_files = self.transac_files(path)

        for transac_file in transaction_files:
            transac_filepath = os.path.join(path, transac_file)
            src_number, transactions = self._read_transactions_file(transac_filepath, account_book)
            account = account_book.get_by_number(src_number)

            for t in transactions:
                account.submit_transaction(t)
                missing_csv_group.submit_transaction(t)
                check_add_to_env_group(env, t, group_accounts)

        if add_env_group:
            return my_account_groups + [env]
        else:
            return my_account_groups

    @staticmethod
    def _read_personal_accounts(path):
        with open(os.path.join(path, "accounts.json"), "r", encoding="utf-8") as file:
            content = json.load(file)
            groups = dict()
            for name, groups_data in content.items():
                groups[name] = [Account(acc["number"], acc["name"], initial=acc.get("initial", "0.0")) for acc in groups_data]
            return groups

    @classmethod
    def read_account_book(cls, path):
        """Read all accounts involved in transactions from the csv files. Merge same accounts when possible.
          Use both account number matching and list of matching stored in the data path
          (under the name account_match.json)"""
        accounts = set()
        for filename in cls.transac_files(path):
            filepath = os.path.join(path, filename)
            for row in parse_belfius_csv_file(filepath):
                accounts.add(Account(sanitize(row[4]), sanitize(row[5])).identifier)

        # extract existing representatives
        match_json_filepath = os.path.join(path, "account_match.json")
        uf = UnionFind.load_from_json(match_json_filepath)

        # read personal accounts and add them to the list (if by chance they were missing)
        accounts_duplicates = list()
        groups = cls._read_personal_accounts(path)
        for name, accs in groups.items():
            accounts = accounts.union({acc.identifier for acc in accs})

        # map account number with account if account number exist
        by_numbers = defaultdict(list)
        for a in accounts:
            if a[0] is not None:
                by_numbers[a[0]].append(a)

        # iterate over saved matches and update match if necessary with number matching.
        for repr in uf.representatives():
            duplicates = uf.find_comp(repr)
            number = repr[0]
            if number in by_numbers:
                if is_iban_be(number):
                    non_iban = unibanize_be(number)
                    duplicates = duplicates.union(by_numbers[non_iban])
                    by_numbers.pop(non_iban)
                duplicates = duplicates.union(by_numbers[number])
                by_numbers.pop(number)

            accounts_duplicates.append((
                Account(*Account.number_name(repr)),
                duplicates
            ))

            accounts = accounts.difference(duplicates)

        for number, others in by_numbers.items():
            accounts_duplicates.append((Account(*others[0]), set(others)))

        for a in accounts:
            accounts_duplicates.append((Account(*a), {}))

        # add accounts to the book
        account_book = AccountBook()
        for acc, dup in accounts_duplicates:
            account_book.add_account(acc, dup)

        # set initial account value for persoal accounts in the book
        for g in groups.values():
            for a in g:
                a_book = account_book[a.identifier]
                a_book.initial = a.initial

        # update saved matches file
        account_book._uf_match.save_to_json(match_json_filepath)

        return account_book

    @classmethod
    def transac_files(cls, path):
        return filter(lambda v: v.endswith(".csv"), os.listdir(path))

    @classmethod
    def _read_transactions_file(cls, filepath, account_book: AccountBook):
        """Update account db as well"""
        fname = os.path.basename(filepath)
        number = fname[:19]
        transactions = list()

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


