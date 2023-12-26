
import csv
from decimal import Decimal
import os
from typing import Dict, Iterable, Set
from impl.belfius import parse_csv_file, parse_date, sanitize, sanitize_number
from parsing.account import Account, AccountBook
from parsing.data_parser import BankParserOrchestrator
from parsing.transaction import Currency, Transaction


def account_tag(a: Account):
    s = ""
    if a.number is not None:
        s += a.number.replace(" ", "")
    return s


def identifier_fn(t: Transaction):
  return "{when}/{valued}/{_from}/{_to}/{amount}".format(
    when=t.when.isoformat(),
    valued=t.metadata["valued_at"].isoformat(),
    _from=account_tag(t.source),
    _to=account_tag(t.dest),
    amount=t.amount)


class IngParserOrchestrator(BankParserOrchestrator):
  ING_FILES_ENCODING = "utf-8-sig"

  def __init__(self, path, accounts_no_csv=None):
    super().__init__(path, accounts_no_csv=accounts_no_csv)

  def get_transaction_files(self, path: str):
    return [
      os.path.join(path, f)
      for f in os.listdir(path) 
      if "." not in f or f.rsplit(".", 1)[1] not in {'pdf', 'json', 'db'}
    ]

  def read_personal_accounts(self, path: str) -> Dict[str, Iterable[Account]]:
    return {}  # no account group

  def read_accounts(self, path: str) -> Set:
    accounts = set()
    for filepath in self.get_transaction_files(path):
      csv_content = list(parse_csv_file(filepath, header_length=1, encoding=self.ING_FILES_ENCODING))
      if len(csv_content) == 0:
        continue
      accounts.add((sanitize_number(csv_content[0][0]), sanitize(csv_content[0][1])))
      for row in csv_content:
        accounts.add(Account(sanitize_number(row[2]), None).identifier)
    return accounts

  def read_transactions_file(self, filepath: str, account_book: AccountBook) -> Iterable[Transaction]:
    """Update account db as well"""
    transactions = list()
    number = None

    for i, row in enumerate(parse_csv_file(filepath, header_length=1, encoding=self.ING_FILES_ENCODING)):
      """
      Column ids:
      -  0: Numéro de compte
      -  1: Nom du compte
      -  2: Compte partie adverse
      -  3: Numéro de mouvement
      -  4: Date comptable
      -  5: Date valeur
      -  6: Montant
      -  7: Devise
      -  8: Libellés
      -  9: Détails du mouvement
      - 10: Message
      """
      my_account = account_book.get_by_number(sanitize_number(row[0]))
      number = my_account.number
      other_acc_nb = sanitize_number(row[2])
      other_acc_name = None
      other_account = account_book[Account(other_acc_nb, other_acc_name).identifier]

      amount = Decimal(row[6].replace(".", "").replace(",", "."))

      if amount == 0:
        continue  # skip informations

      src_account, dest_account = my_account, other_account
      if amount > 0:
        src_account, dest_account = dest_account, src_account

      when = parse_date(row[4]).date()
      t = Transaction(
        amount=amount.copy_abs(),
        src=src_account, dest=dest_account,
        currency=Currency.validate(row[7]),
        when=when,
        id_fn=identifier_fn,
        valued_at=parse_date(row[5]).date(),
        transaction_nb=sanitize(row[3]),
        statement_nb=when.year,
        communication=sanitize(row[8]),
        details=sanitize(row[9]),
        message=sanitize(row[10])
      )

      transactions.append(t)

    return number, transactions
  
  def check_transaction_files(self, path: str):
    for filepath in self.get_transaction_files(path):
      try:
        rows = parse_csv_file(filepath, header_length=0, encoding=self.ING_FILES_ENCODING) # 12 because want to get headers
        for row in rows: # only read header row 
          if row[0] != "Numéro de compte": # check first header
            return False
          break
      except UnicodeDecodeError:
        return False
    return True