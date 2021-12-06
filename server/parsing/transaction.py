from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from enum import Enum

from .account import Account
from .tags import Tag, TagTree


def bisect_right(a, x, lo=0, hi=None, *, key=None):
    """Return the index where to insert item x in list a, assuming a is sorted.
    The return value i is such that all e in a[:i] have e <= x, and all e in
    a[i:] have e > x.  So if x already appears in the list, a.insert(i, x) will
    insert just after the rightmost x already there.
    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """

    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    # Note, the comparison uses "<" to match the
    # __lt__() logic in list.sort() and in heapq.
    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            if x < a[mid]:
                hi = mid
            else:
                lo = mid + 1
    else:
        while lo < hi:
            mid = (lo + hi) // 2
            if x < key(a[mid]):
                hi = mid
            else:
                lo = mid + 1
    return lo


def bisect_left(a, x, lo=0, hi=None, *, key=None):
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.insert(i, x) will
    insert just before the leftmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """

    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    # Note, the comparison uses "<" to match the
    # __lt__() logic in list.sort() and in heapq.
    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            if a[mid] < x:
                lo = mid + 1
            else:
                hi = mid
    else:
        while lo < hi:
            mid = (lo + hi) // 2
            if key(a[mid]) < x:
                lo = mid + 1
            else:
                hi = mid
    return lo


class Currency(Enum):
    EURO = "EUR"
    USDOLLAR = "USD"

    @classmethod
    def get_symbol(cls, currency):
        return {
            cls.EURO.value: "€",
            cls.USDOLLAR.value: "$"
        }[currency]

    @classmethod
    def validate(cls, currency):
        if currency in {c.value for c in Currency}:
            return currency
        else:
            raise ValueError("invalid currency identifier: '{}'".format(currency))


class Transaction(object):
    def __init__(self, amount: Decimal, currency: Currency, when: date, src: Account, dest: Account, id_fn: callable, **metadata):
        """
        Immutable

        Params
        ------
        amount: Decimal
            The amount of money involved in the transaction from :src to :dest (always positive)
        currency: Currency
            The currency
        when: date
            The time when the transaction happened
        _from: Account
            source account
        _to: Account
            dest account
        id_fn: callable
            A function to generate a unique transaction from the transaction itself
        metadata: dict
            Transaction metadata
        """
        assert src != dest
        self._amount = amount
        self._currency = currency
        self._when = when
        self._src = src
        self._dest = dest
        self._id_fn = id_fn
        self._metadata = metadata

    def __repr__(self):
        return "Transaction(id={}, amount={}{}, when={}, from={}, to={})".format(
            self.identifier, self._amount, Currency.get_symbol(self._currency), self._when, self._src.number, self._dest.number)

    @property
    def identifier(self):
        return self._id_fn(self)

    @property
    def source(self):
        return self._src

    @property
    def dest(self):
        return self._dest

    @property
    def amount(self):
        return self._amount

    @property
    def currency(self):
        return self._currency

    @property
    def when(self):
        return self._when

    # TODO make this better: metadata a attributes
    @property
    def metadata(self):
        return self._metadata


class TransactionBook(object):
    def __init__(self):
        """Represent a searchable set of transactions (identifier by their identifier).
        Provide also efficient filtering by date.
        """
        self._transaction_index = dict()
        self._data = list()  # stores the transaction (sorted by (when, identifier))
        self._t_key_fn = lambda tr: (tr.when, tr.identifier)

    def insert(self, t: Transaction, do_raise=False):
        if t.identifier in self._transaction_index:
            if do_raise:
                raise KeyError("transaction already in transaction book")
            else:
                return
        self._transaction_index[t.identifier] = t
        index = bisect_left(self._data, self._t_key_fn(t), key=self._t_key_fn)
        self._data.insert(index, t)

    def delete_by_id(self, identifier):
        t = self._transaction_index.get(identifier)
        if t is None:
            return
        index = bisect_left(self._data, self._t_key_fn(t), key=self._t_key_fn)
        self._data.pop(index)
        self._transaction_index.pop(identifier)

    def get_by_id(self, identifier):
        return self._transaction_index[identifier]

    def has(self, transaction):
        return transaction.identifier in self._transaction_index

    def has_id(self, identifier):
        return identifier in self._transaction_index

    def search_by(self, **query):
        """Search transactions with a query.

        Params:
        -------
        query: dict
            A dictionary mapping key and value to match transactions by. If key is one of the properties of the
            Transaction class i.e. {'identifier', 'source', 'dest', 'amount', 'currency', 'when'} value is matched
            with said property. Otherwise, if key is not one the properties, the key is sought for in the metadata
            and value is matched there. Value are check by exact equality (i.e. ==)

        Returns
        -------
        matching: List[Transaction]
            List of transactions
        """
        attr_query = {
            k: query.pop(k) for k in ["identifier", "source", "dest", "amount", "currency", "when"] if k in query}
        meta_query = query
        matching = list()
        for t in self._data:
            check = True
            for attr_key, attr_val in attr_query.items():
                if hasattr(t, attr_key):
                    check = check and getattr(t, attr_key) == attr_val
            for meta_key, meta_val in meta_query.items():
                if meta_key in t.metadata:
                    check = check and t.metadata[meta_key] == meta_val
            if check:
                matching.append(t)
        return matching

    def between(self, start=None, end=None):
        """Return all transactions for which .when is between start and end (both included in the interval)"""
        if start is not None and end is not None and start > end:
            raise ValueError("incorrect date range ('{}' > '{}')".format(start, end))
        index_l, index_r = 0, len(self)
        if start is not None:
            index_l = bisect_left(self._data, start.when, key=lambda t: t.when)
        if end is not None:
            index_r = bisect_right(self._data, end.when, key=lambda t: t.when)
        return [self._data[i] for i in range(index_l, index_r)]

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
        """item: integer index between [0, len(self)["""
        return self._data[item]

    def __iter__(self):
        for t in self._data:
            yield t

    def merge(self, tbook: TransactionBook, in_place=False):
        """merge current transac book with another book (in place if requested -> within the current book)"""
        #TODO make this O(n) instead of O(n log n)
        new_book = self if in_place else TransactionBook()
        for t in (tbook if in_place else [*tbook, *self]):
            new_book.insert(t)
        return new_book


class TaggedTransactionBook(object):
    def __init__(self, book: TransactionBook, tag_tree: TagTree):
        self._book = book
        self._tag_tree = tag_tree
        self._tagged_transac = dict()

    def add_tag(self, transaction: Transaction, tag: Tag):
        return self.add_tag_by_ids(transaction.identifier, tag.identifier)

    def add_tag_by_ids(self, transac_id, tag_id):
        if transac_id in self._tagged_transac:
            if tag_id != self._tagged_transac[transac_id]:
                raise ValueError("transaction '{}' already has a tag ('{}') but different from '{}'".format(
                    transac_id, self._tag_tree.tag_name(self._tagged_transac[transac_id]), self._tag_tree.tag_name(tag_id)
                ))
        if not self._book.has_id(transac_id):
            raise ValueError("unknown transaction '{}'".format(transac_id))
        if tag_id not in self._tag_tree:
            raise ValueError("invalid tag with id '{}'".format(tag_id))
        self._tagged_transac[transac_id] = tag_id

    @property
    def base_book(self):
        return self._book

    @staticmethod
    def build_from_file(tbook: TransactionBook, tag_tree: TagTree, filepath: str):
        with open(filepath, "r", encoding="utf8") as file:
            loaded = json.load(file)
            book = TaggedTransactionBook(tbook, tag_tree)
            for transac_id, tag_id in loaded.items():
                book.add_tag_by_ids(transac_id, tag_id)
            return book

