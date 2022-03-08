from collections import defaultdict
from decimal import Decimal
from sqlalchemy import and_, func, or_, select
from db.models import AccountGroup, Category, Currency, Transaction
from db.util import tag_tree_from_database, get_tags_descendants, get_tags_at_level 
  
import logging


def group_boundary_transactions_filter(out, sel_group_stmt):
  if out:
    return and_(Transaction.id_source.in_(sel_group_stmt), Transaction.id_dest.notin_(sel_group_stmt))
  else:
    return and_(Transaction.id_dest.in_(sel_group_stmt), Transaction.id_source.notin_(sel_group_stmt))


def incomes_expenses(session, id_group, year=None, month=None):
  sel_group_stmt = select(AccountGroup.id_account).where(AccountGroup.id_group==id_group)

  def make_query(out):
    fields = [func.sum(Transaction.amount).label('total'), Transaction.id_currency]
    group_bys = [Transaction.id_currency]
    filters = []
    
    if year is None:
      fields.append(Transaction.when_year)
      group_bys.append(Transaction.when_year)
    else:
      filters.append(Transaction.when_year==year)

    if month is None:
      fields.append(Transaction.when_month)
      group_bys.append(Transaction.when_month)
    else:
      filters.append(Transaction.when_month==month)

    filters.append(group_boundary_transactions_filter(out, sel_group_stmt))

    query = session.query(*fields)
    query = query.filter(and_(*filters))
    query = query.group_by(*group_bys)    
    
    return query 

  currency_ids = set() 

  def to_dict(results):
    to_return = list()
    for result in results:
      to_return.append({
        "total": result[0],
        "id_currency": result[1]
      })
      if year is None:
        to_return[-1]["year"] = result[2]
      if month is None:
        to_return[-1]["month"] = result[3 if year is None else 2] 
      currency_ids.add(result[1])
    return to_return

  # incomes
  expenses = make_query(True).all()
  incomes = make_query(False).all()
  d_expenses, d_incomes = to_dict(expenses), to_dict(incomes)
  currencies = Currency.query.filter(Currency.id.in_(currency_ids)).all()

  return d_expenses, d_incomes, currencies


def per_category(session, group=None, period_from=None, period_to=None, id_category=None, bucket_level=-1, include_unlabeled=False):
  ##########
  # Filter #
  ##########

  fields = [Transaction.id_category, func.sum(Transaction.amount).label('amount'), Transaction.id_currency]
  group_bys = [Transaction.id_category, Transaction.id_currency]
  filters = list()
  if group is not None:
    sel_group_stmt = select(AccountGroup.id_account).where(AccountGroup.id_group==group)
    filters.append(or_(group_boundary_transactions_filter(out, sel_group_stmt) for out in [True, False]))
  if period_from is not None:
    filters.append(Transaction.when >= period_from)
  if period_to is not None:
    filters.append(Transaction.when <= period_to)

  tag_tree, categories = tag_tree_from_database(return_plain_categories=True)
  categories = {c.id: c.as_dict() for c in categories}
  currencies = {c.id: c.as_dict() for c in Currency.query.all()}

  if id_category is not None:
    descendants = get_tags_descendants(id_category, tree=tag_tree)
    category_condition = Transaction.id_category.in_(descendants)
    if include_unlabeled:
      category_condition = or_(category_condition, Transaction.id_category == None)
    filters.append(category_condition)
  elif not include_unlabeled: 
    filters.append(Transaction.id_category != None)

  ###########
  # Buckets #
  ###########
    
  raw_buckets = session.execute(select(*fields).where(and_(*filters)).group_by(*group_bys))
  raw_buckets = [{
    "id_category": raw_bucket["id_category"], 
    "amount": Decimal(raw_bucket.amount), 
    "category": categories.get(raw_bucket.id_category, None),
    "id_currency": raw_bucket["id_currency"],
    "currency": currencies.get(raw_bucket["id_currency"], None)
  } for raw_bucket in raw_buckets]

  if bucket_level == -1:
    return raw_buckets

  # determine buckets
  at_level = get_tags_at_level(bucket_level, tree=tag_tree)

  if len(at_level) == 0:
    raise ValueError("no category at the given level")

  categ2bucket = dict()
  for id_ in at_level: 
    descendants = get_tags_descendants(id_, tree=tag_tree)

    for desc_id in descendants:
      categ2bucket[desc_id] = id_

  # fill buckets
  # if categ_id is missing
  buckets = dict()
  for raw_bucket in raw_buckets:
    # determine reference category identifier
    raw_bucket_id_category = raw_bucket["id_category"]
    if raw_bucket_id_category not in categ2bucket:
      # leaf category higher than 'level' in the hierarchy -> create a new bucket
      categ2bucket[raw_bucket_id_category] = raw_bucket_id_category
    bucket_ref_id_category = categ2bucket[raw_bucket_id_category]
    bucket_key = (bucket_ref_id_category, raw_bucket["id_currency"])
    if bucket_key not in buckets:
      buckets[bucket_key] = raw_bucket
      if raw_bucket_id_category != bucket_ref_id_category:
        buckets[bucket_key]["category"] = categories.get(bucket_ref_id_category, None)
        buckets[bucket_key]["id_category"] = bucket_ref_id_category
    else:
      buckets[bucket_key]["amount"] += raw_bucket["amount"]

  return list(buckets.values())