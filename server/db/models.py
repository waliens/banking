import enum
import uuid

from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import Column, JSON, Enum, Integer, Date, Float, String, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, noload
from sqlalchemy.sql.expression import and_, select, func, update, or_
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

class AsDictSerializer(object):
    def __init__(self, *fields, **mapping):
        self._fields = fields
        self._mapping = mapping

    def serialize(self, obj):
        out = dict()
        for k in self._fields:
            if hasattr(obj, k):
                out[k] = getattr(obj, k)
        for k, cvt in self._mapping.items():
            if not hasattr(obj, k):
                continue
            raw = getattr(obj, k)
            if raw is not None:
                out[k] = cvt(raw)
        return out

    @staticmethod
    def as_dict_fn():
        return lambda v: v.as_dict() if v is not None else None

    @staticmethod
    def iter_as_dict_fn():
        return lambda iterable: [AsDictSerializer.as_dict_fn()(v) for v in iterable]


def no_load(query, *keys):
  return query.options(noload(*keys))


class User(Base):
    __tablename__  = "user"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

    # NOTE: In a real application make sure to properly hash and salt passwords
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    @staticmethod
    def hash_password_string(password):
        return generate_password_hash(password)

    def as_dict(self):
        return AsDictSerializer("id", "username").serialize(self)


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    id_parent = Column(Integer, ForeignKey('category.id'), nullable=True)
    color = Column(String(255))
    icon = Column(String)

    def __repr__(self):
        return "<Category(id='%d', name='%s', parent='%d', color='%s')>" % (
            self.id, self.name, self.id_parent, self.color)

    def as_dict(self):
        return AsDictSerializer("id", "name", "id_parent", "color", "icon").serialize(self)


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
    initial = Column(Numeric(20, 2), nullable=True)
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
        return self.initial - self.balance_neg + self.balance_pos
    
    @staticmethod
    def _balance_generic_instance(transacs):
        return sum([t.amount for t in transacs])

    def _balance_generic_expr(cls, field):
        # TODO consider also other currencies
        return select([func.sum(Transaction.amount)]).where(and_(cls.id == field, cls.id_currency == Transaction.id_currency)).correlate_except(Transaction).as_scalar()

    __table_args__ = (
        UniqueConstraint('number', 'name', name='account_name_number_unique_constraint'),
    )

    def __repr__(self):
        return "<Account(id='{}', number='{}', name='{}', initial='{}')>".format(
            self.id, self.number, self.name, self.initial)

    def as_dict(self, show_balance=True):
        fields = ["id", "number", "name", "initial"]
        if show_balance:
            fields.append("balance")
        return AsDictSerializer(
            "id", "number", "name", "initial",
            currency=AsDictSerializer.as_dict_fn(), 
            aliases=AsDictSerializer.iter_as_dict_fn()
        ).serialize(self)

    @staticmethod
    def accounts_by_name(name):
        return Account.query.filter(or_(
            Account.name==name, 
            Account.id.in_(select(AccountAlias.id_account).where(AccountAlias.name==name))
        )).all()


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

    id = Column(Integer, primary_key=True)
    custom_id = Column(String(255), unique=True)
    id_source = Column(Integer, ForeignKey('account.id'), nullable=True)
    id_dest = Column(Integer, ForeignKey('account.id'), nullable=True)
    when = Column(Date)
    metadata_ = Column("metadata", JSON)
    amount = Column(Numeric(20, 2))
    id_currency = Column(Integer, ForeignKey('currency.id'))
    id_category = Column(Integer, ForeignKey('category.id', ondelete='SET NULL'), nullable=True)
    data_source = Column(String)

    source = relationship("Account", foreign_keys=[id_source], lazy="joined", back_populates="as_source")
    dest = relationship("Account", foreign_keys=[id_dest], lazy="joined", back_populates="as_dest")
    currency = relationship("Currency", lazy="joined")
    category = relationship("Category", lazy="joined")

    @hybrid_property
    def when_month(self):
        return self.when.month

    @when_month.expression
    def when_month(cls):
        return func.extract('month', cls.when)

    @hybrid_property
    def when_year(self):
        return self.when.year

    @when_year.expression
    def when_year(cls):
        return func.extract('year', cls.when)
    
    def as_dict(self):
        return AsDictSerializer(
            "id", "custom_id", "id_source", "id_dest", "when",
            "metadata_", "amount", "id_currency", "id_category",
            "data_source",
            when=lambda v: v.isoformat(), amount=str,
            **{k: AsDictSerializer.as_dict_fn() for k in ["source", "dest", "currency", "category"]}
        ).serialize(self)

    def __repr__(self):
        return "<Transaction(id='{}', amount='{}')>".format(self.id, self.amount)

    @classmethod
    def noload_query(cls):
        return cls.query.option(noload('source', 'dest', 'currency', 'category'))


class AccountGroup(Base):
    __tablename__ = 'account_group'
    id_group = Column(Integer, ForeignKey('group.id'), primary_key=True)
    id_account = Column(Integer, ForeignKey('account.id'), primary_key=True)
    contribution_ratio = Column(Float, default=1.0)
    
    account = relationship("Account", lazy="joined")

    def as_dict(self):
        return AsDictSerializer(
            "id_group", "id_account", "contribution_ratio", account=AsDictSerializer.as_dict_fn()).serialize(self)

class TransactionGroup(Base):
    __tablename__ = 'transaction_group'
    id_group = Column(Integer, ForeignKey('group.id'), primary_key=True)
    id_transaction = Column(Integer, ForeignKey('transaction.id'), primary_key=True)
    contribution_ratio = Column(Float, default=1.0)

    transaction = relationship("Transaction")

    def as_dict(self):
        return AsDictSerializer(
            "id_group", "id_transaction", "contribution_ratio", transaction=AsDictSerializer.as_dict_fn()).serialize(self)


class Group(Base):
    __tablename__ = "group"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(String(1024))
    
    account_groups = relationship("AccountGroup", lazy="joined")
    transactions = relationship("TransactionGroup")

    def as_dict(self):
        return AsDictSerializer(
            "id", "name", "description", account_groups=AsDictSerializer.iter_as_dict_fn()).serialize(self)


class MLModelState(enum.Enum):
    INVALID = "invalid"
    VALID = "valid"
    TRAINING = "training"
    DELETED = "deleted"


class MLModelFile(Base):
    __tablename__ = "ml_model_file"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    target = Column(String)
    metadata_ = Column("metadata", JSON)
    state = Column(Enum(MLModelState))

    @staticmethod
    def generate_filename():
        return "{}.pkl".format(uuid.uuid4())

    @classmethod
    def get_models_by_state(cls, state: MLModelState, target=None):
        cond = cls.state == state
        if target is not None:
            cond = and_(cond, cls.target == target)
        return cls.query.where(cond).all()

    @classmethod
    def has_models_in_state(cls, state: MLModelState, target=None):
        cond = cls.state == state
        if target is not None:
            cond = and_(cond, cls.target == target)
        return cls.query.where(cond).count() > 0

    @classmethod
    def invalidate_models_stmt(cls, target=None):
        stmt = update(cls)
        filters = [cls.state != MLModelState.DELETED]
        if target is not None:
            filters.append(cls.target == target)
        stmt = stmt.where(and_(*filters))
        stmt = stmt.values(state=MLModelState.INVALID)
        return stmt

    def as_dict(self):
        return AsDictSerializer("id", "filename", "target", "metadata_", state=lambda v: v.name).serialize(self)
