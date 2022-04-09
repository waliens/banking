from collections import defaultdict
from sqlalchemy import Float, and_, or_, select, func, cast, Integer
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

def tag_tree_from_database(return_plain_categories=False):
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
  final_tree = TagTree(tags, roots, id_tree)
  if return_plain_categories:
    return final_tree, categories
  else:
    return final_tree 


def get_tags_at_level(level=0, tree=None):
  if tree is None:
    tree = tag_tree_from_database()

  def get_at_depth(nodes, depth, curr_depth):
    if curr_depth > depth:
      return [] 
    if curr_depth == depth:
      return nodes
    all = list()
    for node in nodes:
      all.extend(get_at_depth(tree.get_children(node), depth, curr_depth+1))
    return all

  return get_at_depth([r.id for r in tree.roots], level, 0)


def get_tags_descendants(identifier, tree=None):
  if tree is None:
    tree = tag_tree_from_database()
  
  def get_children_recur(identifier):
    children = list()
    for child in tree.get_children(identifier):
      children.extend(get_children_recur(child))
    return tree.get_children(identifier) + children

  return [identifier] + get_children_recur(identifier)


def get_transaction_query(account=None, group=None, sort_by=None, account_to=None, account_from=None, date_from=None, date_to=None, order="desc", amount_from=None, amount_to=None, labeled=None):
  """
  Params
  ------
  account: int (default: None)
  group: int (default: None)
  sort_by: str (default: None)
  account_to: int (default: None)
  account_from: int (default: None)
  date_from: date (default: None)
  date_to: date (default: None)
  order: str (default: "desc")
  amount_from: Decimal (default: None)
  amount_to: Decimal (default: None)
  include_labeled: bool (default: False)
  category: int|bool (default: None)
  """
  query = Transaction.query
  filters = []
  if account is not None:
    filters.append(or_(Transaction.id_source == account, Transaction.id_dest == account))
  if group is not None:
    sel_expr = select(AccountGroup.id_account).where(AccountGroup.id_group == group)
    filters.append(or_(Transaction.id_source.in_(sel_expr), Transaction.id_dest.in_(sel_expr)))
  if labeled is not None:
    if not isinstance(labeled, bool):
      filters.append(Transaction.id_category == labeled)
    elif labeled:
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
  if amount_to is not None:
    filters.append(Transaction.amount <= amount_to)
  if amount_from is not None:
    filters.append(Transaction.amount >= amount_from)
    
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


def month_func(field):
  """sqlite comptatible month function"""
  return cast(func.strftime('%m', field), Integer)


def year_func(field):
  """sqlite comptatible month function"""
  return cast(func.strftime('%Y', field), Integer)