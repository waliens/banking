from decimal import Decimal

from sqlalchemy import Column, JSON, Boolean, Integer, Date, String, ForeignKey, TypeDecorator, UniqueConstraint, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True)
    number = Column(String(63), nullable=True)
    name = Column(String(255), nullable=True)
    initial = Column(MyNumeric, nullable=True)

    equivalences = relationship("AccountEquivalence", lazy="joined")

    __table_args__ = (
        UniqueConstraint('number', 'name', name='account_name_number_unique_constraint'),
    )

    def __repr__(self):
        return "<Account(id='{}', number='{}', name='{}')>".format(
            self.id, self.number, self.name)

    def as_dict(self):
        return AsDictSerializer("id", "number", "name", "initial").serialize(self)


class AccountEquivalence(Base):
    __tablename__ = "account_equivalence"

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

    source = relationship("Account", foreign_keys=[id_source], lazy="joined")
    dest = relationship("Account", foreign_keys=[id_dest], lazy="joined")
    currency = relationship("Currency", lazy="joined")
    category = relationship("Category", lazy="joined")

    def as_dict(self):
        return AsDictSerializer("id", "id_source", "id_dest", "when",
                                "metadata_", "amount", "id_currency", "id_category",
                                when=lambda v: v.isoformat(), amount=str,
                                **{k: AsDictSerializer.as_dict_fn()
                                   for k in ["source", "dest", "currency", "category"]}).serialize(self)

    def __repr__(self):
        return "<Account(id='{}')>".format(self.id)


AccountGroup = Table('account_group', Base.metadata,
                     Column('id_group', ForeignKey('group.id')),
                     Column('id_account', ForeignKey('account.id')))


class Group(Base):
    __tablename__ = "group"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(String(1024))
    accounts = relationship("Account", secondary=AccountGroup, lazy="joined")

    def as_dict(self):
        return AsDictSerializer(
            "id", "name", "description", accounts=AsDictSerializer.iter_as_dict_fn()).serialize(self)
