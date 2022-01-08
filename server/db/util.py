from collections import defaultdict
from db.models import Account, Category
from parsing.util import UnionFind
from sqlalchemy.orm import sessionmaker

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
        default=category.default
      )
      if new_tag.parent_id is not None:
          id_tree[new_tag.parent_id].add(identifier)
      else:
          roots.add(identifier)
      tags[identifier] = new_tag
  return TagTree(tags, roots, id_tree)