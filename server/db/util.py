from collections import defaultdict
from sqlalchemy import Float, and_, cast, or_, select
from sqlalchemy.orm import sessionmaker

from parsing.util import UnionFind
from db.models import Account, AccountGroup, Category, Transaction
from parsing.tags import Tag, TagTree

Session = sessionmaker()

def refresh_all(models, sess):
  for m in models:
    sess.refresh(m)


def save(o, sess):
  if hasattr(o, "__len__"):
    sess.bulk_save_objects(o)
  else:
    sess.add(o)
  sess.commit()


def load_account_uf_from_database():
  accounts = Account.query.all()
  uf = UnionFind()

  for account in accounts:
    key = (account.number, account.name)
    uf.add_repres(key)
    for alias in account.aliases:
      eq_key = (alias.number, alias.name)
      uf.add_elem(eq_key, key)
  
  return accounts, uf


def make_metadata_serializable(o):
  cpy = {k: v for k, v in o.items()}
  cpy["valued_at"] = cpy["valued_at"].strftime("%d/%m/%Y")
  return cpy

'''
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    id_parent = Column(Integer, ForeignKey('category.id'), nullable=True)
    color = Column(String(255))
    income = Column(Boolean)
    default = Column(Boolean)
'''

def tag_tree_from_database():
  categories = Category.query.all()
  tags = defaultdict()
  id_tree = defaultdict(set)
  roots = set()
  for category in categories:
      identifier = category.id
      new_tag = Tag(
        name=category.name,
        identifier=identifier,
        parent_id=category.id_parent,
        color=category.color,
        income=category.income,
        default=category.default,
        icon=category.icon
      )
      if new_tag.parent_id is not None:
          id_tree[new_tag.parent_id].add(identifier)
      else:
          roots.add(identifier)
      tags[identifier] = new_tag
  return TagTree(tags, roots, id_tree)


def get_transaction_query(account=None, group=None, category=None, sort_by=None, account_to=None, account_from=None, date_from=None, date_to=None, order="desc"):
  """
  Params
  ------
  account: int (default: None)
  group: int (default: None)
  category: int|bool (default: None)
  sort_by: str (default: None)
  account_to: int (default: None)
  account_from: int (default: None)
  date_from: date (default: None)
  date_to: date (default: None)
  order: str (default: "desc)"
  """
  query = Transaction.query
  filters = []
  if account is not None:
    filters.append(or_(Transaction.id_source == account, Transaction.id_dest == account))
  if group is not None:
    sel_expr = select(AccountGroup.id_account).where(AccountGroup.id_group == group)
    filters.append(or_(Transaction.id_source.in_(sel_expr), Transaction.id_dest.in_(sel_expr)))
  if category is not None:
    if isinstance(category, int):
      filters.append(Transaction.id_category == category)
    else:
      if category:
        filters.append(Transaction.id_category != None)
      else:
        filters.append(Transaction.id_category == None)
  if date_from is not None:
    filters.append(Transaction.when >= date_from)
  if date_to is not None:
    filters.append(Transaction.when <= date_to)
  if account_to is not None:
    filters.append(Transaction.id_dest == account_to)
  if account_from is not None:
    filters.append(Transaction.id_source == account_from)

  query = Transaction.query.filter(and_(*filters))

  if sort_by is not None:
    sort_expr = {
      'when': Transaction.when,
      'amount': Transaction.amount
    }[sort_by]
    if order == "desc":
      sort_expr = sort_expr.desc()
    else:
      sort_expr = sort_expr.asc()
    query = query.order_by(sort_expr)

  return query