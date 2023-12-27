from collections import defaultdict
from typing import Iterable, Tuple
from sqlalchemy import bindparam
from sqlalchemy.dialects.postgresql import insert

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import or_

from db.models import Group, Transaction, TransactionGroup


def auto_attribute_partial_transaction_to_groups(session: Session, transactions):
  # fetch transaction to get db identifiers
  full_transactions = Transaction.query.where(Transaction.custom_id.in_({t.custom_id for t in transactions})).all()
  auto_attribute_transaction_to_groups(session, full_transactions)


def auto_attribute_transaction_to_groups(session: Session, transactions):
  # for all groups, auto register transaction based on account groups
  group_transaction_map = defaultdict(set)
  groups = Group.query.all()
  for group in groups:
    account_ids = {ag.id_account for ag in group.account_groups}
    for transaction in transactions:
      transaction: Transaction = transaction
      if (transaction.id_source in account_ids) or (transaction.id_dest in account_ids):
        group_transaction_map[group.id].add(transaction.id)
  
  return _create_transaction_groups(
    session=session, 
    transaction_groups=[
      (group_id, transaction_id)
      for group_id, transaction_ids_set in group_transaction_map.items()
      for transaction_id in transaction_ids_set
    ],
    # transaction-level contribution ratio set to 1 meaning only 
    # group-level defined contribution ratio will be used unless
    # the transaction-level contribution ratio is changed later
    default_contribution_ratio=1.0
  )


def auto_attribute_transaction_to_groups_by_accounts(session: Session, account_ids: Iterable[int]):
  full_transactions = Transaction.query.where(or_(
    Transaction.id_dest.in_(account_ids),
    Transaction.id_source.in_(account_ids)
  )).all()
  auto_attribute_transaction_to_groups(session, full_transactions)


def _create_transaction_groups(
  session: Session,
  transaction_groups: Iterable[Tuple[int, int]],
  default_contribution_ratio: float=1.0
):
  """Create transaction group entries based on list of tuples
  """
  if len(transaction_groups) == 0:
    return
  stmt = insert(TransactionGroup).values({
    TransactionGroup.id_group: bindparam("gid"),
    TransactionGroup.id_transaction: bindparam("tid"),
    TransactionGroup.contribution_ratio: bindparam("ratio")
  }).on_conflict_do_nothing(index_elements=[TransactionGroup.id_group, TransactionGroup.id_transaction])
  session.execute(stmt, [
    {
      "gid": group_id,
      "tid": transaction_id,
      "ratio": default_contribution_ratio
    } for group_id, transaction_id in transaction_groups
  ])
  session.commit()