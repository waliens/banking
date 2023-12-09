from datetime import date, datetime
from typing import Optional
from collections import defaultdict
from decimal import Decimal
from functools import partial
from sqlalchemy import and_, extract, func, or_, select, case
from sqlalchemy.orm import aliased
from db.models import AccountGroup, Category, Currency, Transaction, TransactionGroup
from db.util import tag_tree_from_database, get_tags_descendants, get_tags_at_level 
  

def _join_account_groups(query, contribution_ratio: bool=True):
  # contribution ratios
  AccountGroupDest = aliased(AccountGroup)
  AccountGroupSource = aliased(AccountGroup)
  query = query.outerjoin(AccountGroupDest, Transaction.id_dest == AccountGroupDest.id_account) \
    .outerjoin(AccountGroupSource, Transaction.id_source == AccountGroupSource.id_account)
  if contribution_ratio:  
    dest_cr_label = case((AccountGroupDest.id_account != None, AccountGroupDest.contribution_ratio), else_=0.0).label("dest_contribution_ratio")
    src_cr_label = case((AccountGroupSource.id_account != None, AccountGroupSource.contribution_ratio), else_=0.0).label("source_contribution_ratio")
    return query, AccountGroupSource, AccountGroupDest, src_cr_label, dest_cr_label
  else:
    return query, AccountGroupSource, AccountGroupDest
  

def _build_labeled_group_aware_amount(src_cr_label, dest_cr_label, label: str="total"):
  cr_diff = func.abs(dest_cr_label - src_cr_label)
  return func.sum(TransactionGroup.contribution_ratio * cr_diff * Transaction.amount).label(label)
  

def _build_period_aggregate_transactions_by_group_query(
  id_group: int,
  expenses: Optional[bool]=None,
  year: Optional[int]=None,
  month: Optional[int]=None
):
  filters = [TransactionGroup.id_group == id_group]
  fields = [Transaction.id_currency]
  group_bys = [Transaction.id_currency]
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
  
  query = select(*fields) \
    .join(TransactionGroup, TransactionGroup.id_transaction == Transaction.id) \
    .group_by(*group_bys)

  query, _, _, src_cr_label, dest_cr_label = _join_account_groups(query, contribution_ratio=True)
  
  if expenses is not None:
    if expenses:
      filters.append(src_cr_label > dest_cr_label)
    else:
      filters.append(src_cr_label < dest_cr_label)

  query = query.add_columns(_build_labeled_group_aware_amount(src_cr_label, dest_cr_label, label="total"))
  query = query.where(*filters)
  
  # compute value expr
  return query

def incomes_expenses(
  session,
  id_group: int,
  year: Optional[int]=None,
  month: Optional[int]=None
):
  """"""
  expense_query = _build_period_aggregate_transactions_by_group_query(id_group, expenses=True, year=year, month=month)
  income_query = _build_period_aggregate_transactions_by_group_query(id_group, expenses=False, year=year, month=month)
  
  currency_ids = set()

  def to_dict(results):
    to_return = list()
    for result in results:
      to_return.append({
        "total": result.total,
        "id_currency": result.id_currency
      })
      if year is None:
        to_return[-1]["year"] = result.when_year
      if month is None:
        to_return[-1]["month"] = result.when_month
      currency_ids.add(result.id_currency)
    return to_return

  # incomes
  expenses = session.execute(expense_query).all()
  incomes = session.execute(income_query).all()

  d_expenses, d_incomes = to_dict(expenses), to_dict(incomes)
  currencies = Currency.query.filter(Currency.id.in_(currency_ids)).all()

  return d_expenses, d_incomes, currencies


def group_boundary_transactions_filter(out, sel_group_stmt):
  if out:
    return and_(Transaction.id_source.in_(sel_group_stmt), Transaction.id_dest.notin_(sel_group_stmt))
  else:
    return and_(Transaction.id_dest.in_(sel_group_stmt), Transaction.id_source.notin_(sel_group_stmt))


def per_category(
  session,
  group: Optional[int]=None,
  income_only: bool=True,
  period_from: Optional[date]=None,
  period_to: Optional[date]=None,
  id_category: Optional[int]=None,
  bucket_level: int=-1,
  include_unlabeled: bool=False,
  period_bucket: Optional[str]=None
):
  """
  Parameters
  ----------
  session:
    Database session
  group:
    identifier of the group  
  income_only: 
    only if group is specified: if True, consider only income wrt this group. Otherwise, only expenses.
  period_from: 
    if specified: only from this date
  period_to: 
    if specified: only to this date
  id_category:
    if specified: consider only transactions tagged with this category and its subcategories
  bucket_level:
    if specified: filter to keep only categories at this depth in the category tree
  include_unlabeled:
    if True, also includes transactions of this group with no categories in the comp
  period_bucket
  """
  ##########
  # Filter #
  ##########
  fields = [Transaction.id_category, Transaction.id_currency]
  group_bys = [Transaction.id_category, Transaction.id_currency]
  joins = list()
  filters = list()
  if group is not None:
    joins.append((TransactionGroup, TransactionGroup.id_transaction == Transaction.id))
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

  # query building
  query = select(*fields)

  if group is not None:
    query, _, _, src_cr_label, dest_cr_label = _join_account_groups(query, contribution_ratio=True)
    if income_only:
      filters.append(src_cr_label < dest_cr_label)
    else:
      filters.append(src_cr_label > dest_cr_label)
    query = query.add_columns(_build_labeled_group_aware_amount(src_cr_label, dest_cr_label, label="amount"))

  query = query.where(*filters).group_by(*group_bys)

  for join_table, join_on in joins:
    query = query.join(join_table, join_on)

  ###########
  # Buckets #
  ###########
    
  results = session.execute(query)
  raw_buckets = defaultdict(list)
  for raw_entry in results:
    actual_data = {
      "id_category": raw_entry.id_category, 
      "amount": Decimal(raw_entry.amount), 
      "category": categories.get(raw_entry.id_category, None),
      "id_currency": raw_entry.id_currency,
      "currency": currencies.get(raw_entry.id_currency, None),
    }
    if period_bucket is None:  # only one list stored at index -1
      raw_buckets[-1].append(actual_data)
    else:
      raw_buckets[getattr(raw_entry, period_bucket)].append(actual_data)

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
    curr_buckets = buckets[int(top_level_bucket_key)]
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
