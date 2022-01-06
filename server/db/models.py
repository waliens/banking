from abc import ABCMeta, abstractmethod
from decimal import Decimal

from sqlalchemy import Column, JSON, Boolean, Integer, Date, Float, String, ForeignKey, TypeDecorator, UniqueConstraint, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import column_property, relationship, foreign, remote
from sqlalchemy.sql.expression import and_, select, func, cast, column, table
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

class AsDictSerializer(object):
    def __init__(self, *fields, **mapping):
        self._fields = fields
        self._mapping = mapping

    def serialize(self, obj):
        out = dict()
        for k in self._fields:
            out[k] = getattr(obj, k)
        for k, cvt in self._mapping.items():
            raw = getattr(obj, k)
            if raw is not None:
                out[k] = cvt(raw)
        return out

    @staticmethod
    def as_dict_fn():
        return lambda v: v.as_dict()

    @staticmethod
    def iter_as_dict_fn():
        return lambda iterable: [AsDictSerializer.as_dict_fn()(v) for v in iterable]


class MyNumeric(TypeDecorator):
    impl = String

    def __init__(self, length=None, **kwargs):
        super().__init__(length, **kwargs)

    def process_literal_param(self, value: Decimal, dialect):
        return str(value) if value is not None else None

    process_bind_param = process_literal_param

    def process_result_value(self, value, dialect):
        # convert sql string to python time
        return Decimal(value) if value is not None else None


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    id_parent = Column(Integer, ForeignKey('category.id'), nullable=True)
    color = Column(String(255))
    income = Column(Boolean)
    default = Column(Boolean)

    def __repr__(self):
        return "<Account(id='%d', name='%s', parent='%d', color='%s')>" % (
            self.id, self.name, self.parent_category, self.color)

    def as_dict(self):
        return AsDictSerializer("id", "name", "id_parent", "color", "income", "default").serialize(self)


class Currency(Base):
    __tablename__ = "currency"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(15))
    short_name = Column(String(255))
    long_name = Column(String(255))

    def __repr__(self):
        return "<Currency(id='%d', symbol='%s', short_name='%s', short_name='%s')>" % (
            self.id, self.symbol, self.short_name, self.long_name)

    def as_dict(self):
        return AsDictSerializer("id", "symbol", "short_name", "long_name").serialize(self)

    @staticmethod
    def short_name_to_id(default="EUR"):
        currencies = Currency.query.filter(Currency.short_name == default).all()
        assert len(currencies) == 1
        return currencies[0].id


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True)
    number = Column(String(63), nullable=True)
    name = Column(String(255), nullable=True)
    initial = Column(MyNumeric, nullable=True)
    id_currency = Column(Integer, ForeignKey('currency.id'))

    as_source = relationship(lambda: Transaction, foreign_keys=lambda: Transaction.id_source, back_populates="source")
    as_dest = relationship(lambda: Transaction, foreign_keys=lambda: Transaction.id_dest, back_populates="dest")
    aliases = relationship("AccountAlias", lazy="joined")
    currency = relationship("Currency", lazy="joined")

    @hybrid_property
    def balance_pos(self):
        return self._balance_generic_instance(self.as_dest)
    
    @balance_pos.expression
    def balance_pos(cls):
        return cls._balance_generic_expr(Transaction.id_dest)

    @hybrid_property
    def balance_neg(self):
        return self._balance_generic_instance(self.as_source)

    @balance_neg.expression
    def balance_neg(cls):
        return cls._balance_generic_expr(Transaction.id_source)

    @hybrid_property
    def balance(self):
        return self.initial - Decimal(str(self.balance_neg)) + Decimal(str(self.balance_pos))
    
    @staticmethod
    def _balance_generic_instance(transacs):
        return sum([t.amount for t in transacs])

    def _balance_generic_expr(cls, field):
        # TODO consider also other currencies
        return select([func.sum(Transaction.amount.cast(Float))]).where(and_(cls.id == field, cls.id_currency == Transaction.id_currency)).correlate_except(Transaction).as_scalar()

    __table_args__ = (
        UniqueConstraint('number', 'name', name='account_name_number_unique_constraint'),
    )

    def __repr__(self):
        return "<Account(id='{}', number='{}', name='{}', initial='{}')>".format(
            self.id, self.number, self.name, self.initial)

    def as_dict(self):
        return AsDictSerializer("id", "number", "name", "initial", "balance",
                                currency=AsDictSerializer.as_dict_fn(), 
                                aliases=AsDictSerializer.iter_as_dict_fn()).serialize(self)

class AccountAlias(Base):
    __tablename__ = "account_alias"

    id = Column(Integer, primary_key=True)
    number = Column(String(63), nullable=True)
    name = Column(String(255), nullable=True)
    id_account = Column(Integer, ForeignKey('account.id', ondelete="CASCADE"))

    def as_dict(self):
        return AsDictSerializer("id", "number", "name", "id_account").serialize(self)


class Transaction(Base):
    __tablename__ = 'transaction'

    id = Column(String(255), primary_key=True)
    id_source = Column(Integer, ForeignKey('account.id'))
    id_dest = Column(Integer, ForeignKey('account.id'))
    when = Column(Date)
    metadata_ = Column("metadata", JSON)
    amount = Column(MyNumeric)
    id_currency = Column(Integer, ForeignKey('currency.id'))
    id_category = Column(Integer, ForeignKey('category.id'), nullable=True)

    source = relationship("Account", foreign_keys=[id_source], lazy="joined", back_populates="as_source")
    dest = relationship("Account", foreign_keys=[id_dest], lazy="joined", back_populates="as_dest")
    currency = relationship("Currency", lazy="joined")
    category = relationship("Category", lazy="joined")

    def as_dict(self):
        return AsDictSerializer("id", "id_source", "id_dest", "when",
                                "metadata_", "amount", "id_currency", "id_category",
                                when=lambda v: v.isoformat(), amount=str,
                                **{k: AsDictSerializer.as_dict_fn()
                                   for k in ["source", "dest", "currency", "category"]}).serialize(self)

    def __repr__(self):
        return "<Transaction(id='{}', amount='{}')>".format(self.id, self.amount)


class AccountGroup(Base):
    __tablename__ = 'account_group'
    id_group = Column(Integer, ForeignKey('group.id'), primary_key=True)
    id_account = Column(Integer, ForeignKey('account.id'), primary_key=True)


class Group(Base):
    __tablename__ = "group"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(String(1024))
    accounts = relationship("Account", secondary='account_group', lazy="joined")

    def as_dict(self):
        return AsDictSerializer(
            "id", "name", "description", accounts=AsDictSerializer.iter_as_dict_fn()).serialize(self)
