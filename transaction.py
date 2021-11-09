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

    # TODO make this better
    @property
    def metadata(self):
        return self._metadata

