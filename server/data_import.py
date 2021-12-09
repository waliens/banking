from operator import eq
import os

from sqlalchemy import update, delete
from sqlalchemy.sql.expression import bindparam

from db.models import Account, AccountEquivalence, AccountGroup, Currency, Transaction
from db.util import load_account_uf_from_database, make_metadata_serializable, save, refresh_all
from impl.belfius import BelfiusParserOrchestrator
from parsing.util import group_by
from server.parsing.account import AccountBook


def save_diff_db_parsed_accounts(db_accounts, account_book: AccountBook, sess):
  reference_accounts_set = {(a.number, a.name) for a in account_book.accounts}
  all_db_accounts = {**db_accounts}
  removed = [a for k, a in db_accounts.items() if k not in reference_accounts_set]
  
  # create new accounts
  new = [Account(number=a.number, name=a.name, initial=0) for a in account_book.accounts if a.identifier not in set(all_db_accounts.keys())]
  sess.bulk_save_objects(new, return_defaults=True)
  sess.commit()
  all_db_accounts.update({(a.number, a.name): a for a in new})

  replacer = [all_db_accounts[account_book[(a.number, a.name)].identifier] for a in removed]
  old_new_ids = [{'old_id': rm_acc.id, 'new_id': rep_acc.id} for rm_acc, rep_acc in zip(removed, replacer)]

  if len(old_new_ids) > 0:
    # update references of to-be deleted accounts in other tables
    update_id_dest_stmt = update(Transaction).where(Transaction.id_dest == bindparam('old_id')).values({Transaction.id_dest: bindparam('new_id')})
    update_id_src_stmt = update(Transaction).where(Transaction.id_source == bindparam('old_id')).values({Transaction.id_source: bindparam('new_id')})
    update_id_in_group_stmt = update(AccountGroup).where(AccountGroup.c.id_account == bindparam('old_id')).values({AccountGroup.c.id_account: bindparam('new_id')})

    sess.execute(update_id_dest_stmt, old_new_ids)
    sess.execute(update_id_src_stmt, old_new_ids)
    sess.execute(update_id_in_group_stmt, old_new_ids)

  if len(removed) > 0:
    delete_stmt = delete(Account).where(Account.id == bindparam('old_id'))
    sess.execute(delete_stmt, [{'old_id': a.id} for a in removed])

    for a in removed:
      all_db_accounts.pop((a.number, a.name)) 

  if len(removed) > 0 or len(old_new_ids) > 0:
    sess.commit()

  db_equivalences = group_by(AccountEquivalence.query.all(), key=lambda m: m.id_account)
  equivalences = list()

  for acc_key, acc in all_db_accounts.items():
    similar = account_book._uf_match.find_comp(acc_key)
    db_sim = {(equiv.number, equiv.name) for equiv in db_equivalences.get(acc.id, [])}
    missing = similar.difference(db_sim).difference({acc_key})
    equivalences.extend([AccountEquivalence(number=e[0], name=e[1], id_account=acc.id) for e in missing])

  sess.bulk_save_objects(equivalences)
  sess.commit()

  return all_db_accounts


def import_beflius_csv(dirname, sess):
  db_accounts, uf = load_account_uf_from_database()
  db_accounts = {(a.number, a.name): a for a in db_accounts}
  uf.save_to_json(os.path.join(dirname, "account_match.json"))
  parser = BelfiusParserOrchestrator()
  groups = parser.read(dirname, add_env_group=True)
  env = groups[0]
  
  db_accounts = save_diff_db_parsed_accounts(db_accounts, env.account_book, sess=sess)
  currencies = Currency.query.all()

  existing_ids = {v[0] for v in sess.query(Transaction.id).all()}

  # transactions
  transacs = list()
  for t in groups[0].transaction_book:
    if t.identifier in existing_ids:
      continue  # skip existing transactions
    transacs.append(Transaction(
      id=t.identifier,
      id_source=db_accounts[t.source.identifier].id,
      id_dest=db_accounts[t.dest.identifier].id,
      when=t.when,
      metadata_=make_metadata_serializable(t.metadata),
      amount=t.amount,
      id_currency=[c for c in currencies if t.currency == c.short_name][0].id,
      id_category=None)
    )
    
  save(transacs, sess=sess)
