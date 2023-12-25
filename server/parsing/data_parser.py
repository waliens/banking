import json
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, Iterable, Set

from parsing.util import UnionFind

from .account import (Account, AccountBook, AccountGroup, is_iban_be,
                      is_noniban_be, unibanize_be)
from .transaction import Transaction


def check_add_to_env_group(env_group: AccountGroup, t: Transaction, excluded_identifiers: set):
  """Check whether the current transaction should be added to the environment by checking excluded account numbers.
  If source or dest is not in excluded numbers than env_group is update to contain the account(s) and the transaction.

  Params
  ------
  env_group: AccountGroup
  t: Transaction
  excluded_identifiers: set

  Returns
  -------
  added: bool
    True if the transaction was added to the env group
  """
  if t.source.identifier not in excluded_identifiers and t.source.identifier not in env_group:
    env_group.add_account(t.source)
  if t.dest.identifier not in excluded_identifiers and t.dest.identifier not in env_group:
    env_group.add_account(t.dest)
  return env_group.submit_transaction(t)


class ParserOrchestrator(ABC):
  @abstractmethod
  def read(self, path, add_env_group=False):
    """
    Params:
    -------
    path: str
      Path of a root folder containing all data needed to set up transactions, accounts and groups
    add_env_group: bool
      True to include an environment account group

    Returns:
    --------
    groups: A list of account groups
      The parsed transaction
    """
    pass


class BankParserOrchestrator(ParserOrchestrator):
  """Transaction data as csv files per account. Account groups read from json file.
  Possible to specify accounts which have no csv file, in this case, specify them in accounts_no_csv.
  """
  def __init__(self, workdir: str, accounts_no_csv=None):
    self._workdir = workdir
    self._accounts_no_csv = {} if accounts_no_csv is None else set(accounts_no_csv)

  @property
  def workdir(self):
    return self._workdir
    
  def read(self, read_path, add_env_group=False):
    # read accounts from the csv files
    account_book = self.read_account_book()

    # read personal accounts and create groups
    groups = self.read_personal_accounts(self.workdir)
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
    for filepath in self.get_transaction_files(read_path):
      src_number, transactions = self.read_transactions_file(filepath, account_book)
      account = account_book.get_by_number(src_number)

      for t in transactions:
        account.submit_transaction(t)
        missing_csv_group.submit_transaction(t)
        check_add_to_env_group(env, t, group_accounts)

    if add_env_group:
      return my_account_groups + [env]
    else:
      return my_account_groups

  def read_account_book(self):
    """Read all accounts involved in transactions from the csv files. Merge same accounts when possible.
      Use both account number matching and list of matching stored in the data path
      (under the name account_match.json)"""
    accounts = self.read_accounts(self.workdir)

    # extract existing representatives
    match_json_filepath = os.path.join(self.workdir, "account_match.json")
    uf = UnionFind.load_from_json(match_json_filepath)

    # read personal accounts and add them to the list (if by chance they were missing)
    groups = self.read_personal_accounts(self.workdir)
    accounts_duplicates = list()
    accounts = accounts.union({
      acc.identifier 
      for _, accs in groups.items() 
      for acc in accs
    })

    # map account number with account if account number exist
    by_numbers = defaultdict(list)
    for a in accounts:
      if a[0] is not None:
        by_numbers[a[0]].append(a)

    # create first uf by matching representatives by numbers
    uf_number = UnionFind()
    for number, accs in by_numbers.items():
      acc_repr, acc_dupl = accs[0], accs[1:]
      if is_iban_be(number) and unibanize_be(number) in by_numbers:
        non_iban = unibanize_be(number)
        non_iban_account = by_numbers[non_iban][0]
        non_iban_repr = uf_number.find_repr(non_iban_account)
        if non_iban_repr is not None:  # non iban has been added already, change repr to iban
          uf_number.update_repr(non_iban_repr, acc_repr)
        else:
          uf_number.add_repres(acc_repr)
      else:
        uf_number.add_repres(acc_repr)
      for dupl in acc_dupl:
        uf_number.add_elem(dupl, acc_repr)
      
    # merge uf number with json uf
    for nb_repr in uf_number.representatives():
      # find the final representative
      repr = None
      uf_repr = uf.find_repr(nb_repr)
      if uf_repr is not None:
        repr = uf_repr
      else:
        nb_comp = uf_number.find_comp(nb_repr)
        reprs_from_comp = {uf.find_repr(c) for c in nb_comp if uf.find_repr(c) is not None}
        if len(reprs_from_comp) > 1:
          raise ValueError("match several different accounts: {}".format(reprs_from_comp))
        elif len(reprs_from_comp) == 1:
          repr = list(reprs_from_comp)[0]
      if repr is None:  # missing from json uf
        # try matching by the account numbers
        number = nb_repr[0]
        exact_match_repr = {uf.find_repr(r) for r in uf.keys() if r[0] == number}
        non_iban_in_json_repr = {uf.find_repr(r) for r in uf.keys() if (is_iban_be(number) and unibanize_be(number) == r[0])}
        iban_in_json_repr = {uf.find_repr(r) for r in uf.keys() if (r[0] is not None and is_noniban_be(number) and is_iban_be(r[0]) and unibanize_be(r[0]) == number)}
        if len(exact_match_repr) == 1:
          repr = list(exact_match_repr)[0]
        elif len(non_iban_in_json_repr) == 1:
          uf.update_repr(list(non_iban_in_json_repr)[0], nb_repr)
          repr = nb_repr
        elif len(iban_in_json_repr) == 1:
          repr = list(iban_in_json_repr)[0]
        elif len(exact_match_repr) > 1 or len(non_iban_in_json_repr) > 1 or len(iban_in_json_repr) > 1:
          raise ValueError("several match for: {}".format(nb_repr))
      if repr is None:
        repr = nb_repr
      
      # final duplicates
      duplicates = {repr, nb_repr}
      duplicates = duplicates.union(uf_number.find_comp(nb_repr))
      if repr in uf: 
        duplicates = duplicates.union(uf.find_comp(repr))
      
      if repr != nb_repr:
        uf.add_elem(nb_repr, repr)
      elif repr not in uf:
        uf.add_repres(repr)
      
      for dupl in duplicates:
        if dupl not in uf.find_comp(repr):
          uf.add_elem(dupl, repr)

    # iterate over saved matches and update match if necessary with number matching.
    for repr in uf.representatives():
      duplicates = uf.find_comp(repr)
      accounts_duplicates.append((
        Account(*Account.number_name(repr)),
        duplicates
      ))
      accounts = accounts.difference(duplicates)

    for a in accounts:
      accounts_duplicates.append((Account(*a), {}))

    # add accounts to the book
    account_book = AccountBook()
    for acc, dup in accounts_duplicates:
      account_book.add_account(acc, dup)

    # set initial account value for personal accounts in the book
    for g in groups.values():
      for a in g:
        a_book = account_book[a.identifier]
        a_book.initial = a.initial

    # update saved matches file
    account_book._uf_match.save_to_json(match_json_filepath)

    return account_book

  @abstractmethod
  def get_transaction_files(self, path: str) -> Iterable[str]:
    pass

  @abstractmethod
  def read_personal_accounts(self, path: str) -> Dict[str, Iterable[Account]]:
    pass 

  @abstractmethod
  def read_accounts(self, path: str) -> Set:
    pass

  @abstractmethod
  def read_transactions_file(self, filepath, account_book: AccountBook) -> Iterable[Transaction]:
    pass

