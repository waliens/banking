from __future__ import annotations
import bisect
from datetime import datetime
from decimal import Decimal
from enum import Enum

from account import Account


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
    def __init__(self, amount: Decimal, currency: Currency, when: datetime, src: Account, dest: Account, id_fn: callable, **metadata):
        """
        Immutable

        Params
        ------
        amount: Decimal
            The amount of money involved in the transaction from :src to :dest (always positive)
        currency: Currency
            The currency
        when: Datetime
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
        index = bisect.bisect_left(self._data, self._t_key_fn(t), key=self._t_key_fn)
        self._data.insert(index, t)

    def delete_by_id(self, identifier):
        t = self._transaction_index.get(identifier)
        if t is None:
            return
        index = bisect.bisect_left(self._data, self._t_key_fn(t), key=self._t_key_fn)
        self._data.pop(index)
        self._transaction_index.pop(identifier)

    def get_by_id(self, identifier):
        return self._transaction_index[identifier]

    def search_by(self, **query):
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
        if start is not None and end is not None and start > end:
            raise ValueError("incorrect date range ('{}' > '{}')".format(start, end))
        index_l, index_r = 0, len(self)
        if start is not None:
            index_l = bisect.bisect_left(self._data, start.when, key=lambda t: t.when)
        if end is not None:
            index_r = bisect.bisect_right(self._data, end.when, key=lambda t: t.when)
        return [self._data[i] for i in range(index_l, index_r)]

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
        return self._data[item]

    def __iter__(self):
        for t in self._data:
            yield t

    def merge(self, tbook: TransactionBook, in_place=False):
        """merge current transac book with other book (in place if requested) -> within the current book)"""
        #TODO make this O(n) instead of O(n log n)
        new_book = self if in_place else TransactionBook()
        for t in (tbook if in_place else [*tbook, *self]):
            new_book.insert(t)
        return new_book
