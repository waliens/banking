import abc
import re
from decimal import Decimal

from .util import UnionFind, JsonSerializable


def is_iban(s):
    regex = r"[a-zA-Z]{2}[0-9]{2}[a-zA-Z0-9]{4}[0-9]{7}([a-zA-Z0-9]?){0,16}"
    return re.match(regex, s.replace(" ", ""), re.IGNORECASE) is not None


def is_noniban_be(s):
    return re.match(r"[0-9]{3}-[0-9]{7}-[0-9]{2}", s) is not None


def is_iban_be(s):
    return is_iban(s) and s.startswith("BE")


def ibanize(s, prefix):
    no_space = prefix + s.replace("-", "")
    return " ".join([no_space[i:(i+4)] for i in range(0, 16, 4)])


def unibanize_be(number):
    digits = re.sub(r"[\s-]+", "", number)[-12:]
    return "{}-{}-{}".format(digits[:3], digits[3:10], digits[-2:])


class Transactionable(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr(subclass, 'submit_transaction') and callable(subclass.submit_transaction) or NotImplemented

    @abc.abstractmethod
    def submit_transaction(self, t) -> bool:
        """Submit a transaction.

        Params
        ------
        t: Transaction
            A transaction

        Returns
        -------
        committed: bool
            True if the transaction invoved the current object in one way or another
        """
        raise NotImplementedError


class Account(Transactionable, JsonSerializable):
    def __init__(self, number: str = None,  name: str = None, initial: str = None):
        """"""
        from .transaction import TransactionBook
        self._history = TransactionBook()
        self._balance = Decimal()
        self._initial = Decimal() if initial is None else Decimal(initial)
        self._number = number
        self._name = name

    def __repr__(self):
        return "Account(identifier={}, number={}, balance={}, name={}, n_trans={})".format(
            self.identifier, self._number, self._balance, self._name, len(self._history))

    def __cmp__(self, other):
        return isinstance(other, Account) and other.identifier == self.identifier

    @property
    def initial(self):
        return self._initial

    @initial.setter
    def initial(self, val):
        self._initial = Decimal(val)

    @classmethod
    def number_name(cls, identifier):
        return identifier[0], identifier[1]

    @property
    def balance(self):
        return self._balance + self._initial

    @property
    def identifier(self):
        return self._number, self._name

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, v):
        self._number = v

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, v):
        self._name = v

    @property
    def history(self):
        return self._history

    def submit_transactions(self, transactions):
        """
        Returns:
        --------
        committed: iterable of bool
            committed[i] is True if the transactions[i] was committed to the account
        """
        for t in transactions:
            self.submit_transaction(t)

    def _eval_transaction(self, t):
        """
        Eval a transaction and commit it to the account if the account is involved

        Params
        ------
        t: Transaction
            A transaction

        Returns
        -------
        committed: bool
            True if the transaction was commited to the account
        """
        is_source = t.source.identifier == self.identifier
        is_dest = t.dest.identifier == self.identifier
        if is_source:
            self._balance -= t.amount
        elif is_dest:
            self._balance += t.amount
        if is_source or is_dest:
            self._history.insert(t, do_raise=False)
            return True
        else:
            return False

    def submit_transaction(self, t) -> bool:
        return self._eval_transaction(t)

    def __iter__(self):
        """iterator of transaction history"""
        for t in self._history:
            yield t

    def diff_between(self, start=None, end=None):
        amount = Decimal()
        for t in self._history.between(start=start, end=end):
            if t.source.identifier == self.identifier:
                amount -= t.amount
            elif t.dest.identifier == self.identifier:
                amount += t.amount
        return amount


class AccountBook(object):
    """ A dictionary of accounts, mapping account identifier to account"""
    def __init__(self):
        self._uf_match = UnionFind()
        self._numbers_index = dict()
        self._accounts = dict()

    @property
    def accounts(self):
        return self._accounts.values()

    def add_account(self, account, duplicates=None):
        acc_repr = self._uf_match.find_repr(account.identifier)
        if acc_repr is None:
            self._accounts[account.identifier] = account
            self._uf_match.add_repres(account.identifier)
            self._numbers_index[account.number] = account
        duplicates_diff = set(duplicates).difference(self._uf_match.find_comp(account.identifier))
        for a in duplicates_diff:
            if a == account.identifier:
                continue
            self._uf_match.add_elem(a, account.identifier)
            self._numbers_index[a[0]] = account

    def _change_repr(self, old_identifier, new_account):
        """Change the old representative account to become new (in _uf_match and _accounts). The stored account
        object is updated and :new_account is not added to the structure

        Returns
        -------
        updated: Account
            The updated account
        """
        if old_identifier not in self._uf_match \
                and self._uf_match.find_repr(old_identifier) == old_identifier:
            raise ValueError("old '{}' is not a representative".format(old_identifier))
        self._uf_match.update_repr(old_identifier, new_account.identifier)
        old_account = self._accounts.pop(old_identifier)
        old_account.name = new_account.name
        old_account.number = new_account.number
        self._accounts[old_account.identifier] = old_identifier
        return old_account

    def __getitem__(self, item):
        if item in self._accounts:
            return self._accounts[item]
        else:
            return self._accounts[self._uf_match[item]]

    def __len__(self):
        return len(self._accounts)

    def __contains__(self, item):
        return item in self._accounts or (item in self._uf_match and self._uf_match[item] in self._accounts)

    def __iter__(self):
        for a in self.accounts:
            yield a

    def get_by_match(self, account):
        if account.identifier in self:
            return self[account.identifier]
        elif account.number in self._numbers_index:
            return self.get_by_number(account.number)
        else:
            return None  # no match

    def get_by_number(self, number):
        return self._numbers_index.get(number)

    def search_by_name(self, q):
        pattern = re.compile(".*" + q + ".*")
        matches = list()
        for a in self:
            for i in self._uf_match.find_comp(a.identifier):
                if i[1] is not None and pattern.match(i[1]) is not None:
                    matches.append(a)
                    break
        return matches


class AccountGroup(Transactionable):
    """A transactionable group of accounts with a name"""
    def __init__(self, accounts: set, book: AccountBook, name: str = None):
        self._book = book
        self._accounts = accounts
        self._name = name

    def add_account(self, account):
        if account.identifier not in self._book:
            raise ValueError("unknown account")
        self._accounts.add(account.identifier)

    def __getitem__(self, item):
        if item not in self._accounts:
            raise KeyError("account not in group")
        return self._book[item]

    def __contains__(self, item):
        return item in self._accounts

    def __len__(self):
        return len(self._accounts)

    def __iter__(self):
        for _id in self._accounts:
            yield self._book[_id]

    def get_by_number(self, number):
        if number is None or number not in {a[0] for a in self._accounts}:
            raise ValueError("account number missing in group")
        return self._book.get_by_number(number)

    @property
    def accounts(self):
        return [a for a in self]

    @property
    def balance(self):
        return sum([a.balance for a in self])

    def submit_transactions(self, transactions):
        return [self.submit_transaction(t) for t in transactions]

    def submit_transaction(self, t) -> bool:
        if not (t.source.identifier in self or t.dest.identifier in self):
            return False
        if t.source.identifier in self:
            self[t.source.identifier].submit_transaction(t)
        if t.dest.identifier in self:
            self[t.dest.identifier].submit_transaction(t)
        return True

    @property
    def account_book(self):
        return self._book

    @property
    def transaction_book(self):
        from .transaction import TransactionBook
        tbook = TransactionBook()
        for account in self:
            tbook.merge(account.history, in_place=True)
        return tbook

    @property
    def name(self):
        return self._name
