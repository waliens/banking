from collections import defaultdict
from decimal import Decimal
from functools import partial
from sqlalchemy import and_, extract, func, or_, select
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


def per_category(session, group=None, period_from=None, period_to=None, id_category=None, bucket_level=-1, include_unlabeled=False, period_bucket=None):
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
  if period_bucket is not None:
    if period_bucket == "month":
      bucket_fn = partial(extract, 'month')
    elif period_bucket == "year":
      bucket_fn = partial(extract, 'year')
    else:
      raise ValueError("incorrect period bucket name '{}'".format(period_bucket))
    fields.append(bucket_fn(Transaction.when).label(period_bucket))
    group_bys.append(bucket_fn(Transaction.when))

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
    
  results = session.execute(select(*fields).where(and_(*filters)).group_by(*group_bys))
  raw_buckets = defaultdict(list)
  for raw_entry in results:
    actual_data = {
      "id_category": raw_entry["id_category"], 
      "amount": Decimal(raw_entry.amount), 
      "category": categories.get(raw_entry.id_category, None),
      "id_currency": raw_entry["id_currency"],
      "currency": currencies.get(raw_entry["id_currency"], None),
    }
    if period_bucket is None:  # only one list stored at index -1
      raw_buckets[-1].append(actual_data)
    else:
      raw_buckets[raw_entry[period_bucket]].append(actual_data)

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
  buckets = defaultdict(dict)
  for top_level_bucket_key, bottom_level_buckets in raw_buckets.items():
    curr_buckets = buckets[top_level_bucket_key]
    for bottom_level_bucket in bottom_level_buckets:
      # determine reference category identifier
      bottom_level_bucket_id_category = bottom_level_bucket["id_category"]
      if bottom_level_bucket_id_category not in categ2bucket:
        # leaf category higher than 'level' in the hierarchy -> create a new bucket
        categ2bucket[bottom_level_bucket_id_category] = bottom_level_bucket_id_category
      bucket_ref_id_category = categ2bucket[bottom_level_bucket_id_category]
      bucket_key = (bucket_ref_id_category, bottom_level_bucket["id_currency"])
      if bucket_key not in curr_buckets:
        curr_buckets[bucket_key] = bottom_level_bucket
        if bottom_level_bucket_id_category != bucket_ref_id_category:
          curr_buckets[bucket_key]["category"] = categories.get(bucket_ref_id_category, None)
          curr_buckets[bucket_key]["id_category"] = bucket_ref_id_category
      else:
        curr_buckets[bucket_key]["amount"] += bottom_level_bucket["amount"]

  return {k: list(v.values()) for k, v in buckets.items()}