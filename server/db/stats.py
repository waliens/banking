from cmath import exp
from numpy import extract
from sqlalchemy import and_, func, select
from db.models import AccountGroup, Currency, Transaction
  
import logging

def group_boundary_transactions(out, query, sel_group_stmt):
  if out:
    filter_ = and_(Transaction.id_source.in_(sel_group_stmt), Transaction.id_dest.notin_(sel_group_stmt))
  else:
    filter_ = and_(Transaction.id_dest.in_(sel_group_stmt), Transaction.id_source.notin_(sel_group_stmt))
  return query.filter(filter_)


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

    query = session.query(*fields)
    query = group_boundary_transactions(out, query, sel_group_stmt)
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

