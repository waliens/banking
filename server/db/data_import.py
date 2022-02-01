from ast import parse
import logging
from operator import eq
import os

from sqlalchemy import update, delete
from sqlalchemy.sql.expression import bindparam

from db.models import Account, AccountAlias, AccountGroup, AsDictSerializer, Currency, Transaction
from db.util import load_account_uf_from_database, make_metadata_serializable, save
from impl.belfius import BelfiusParserOrchestrator
from parsing.util import group_by
from parsing.account import AccountBook

from impl.mastercard import ms_identifier, parse_folder, parse_mastercard_pdf


def save_diff_db_parsed_accounts(db_accounts, account_book: AccountBook, sess):
  reference_accounts_set = {(a.number, a.name) for a in account_book.accounts}
  all_db_accounts = {**db_accounts}
  removed = [a for k, a in db_accounts.items() if k not in reference_accounts_set]
  id_default_currency = Currency.short_name_to_id("EUR")
  
  # create new accounts
  new = [Account(number=a.number, name=a.name, initial=0, id_currency=id_default_currency) for a in account_book.accounts if a.identifier not in set(all_db_accounts.keys())]
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

  db_aliases = group_by(AccountAlias.query.all(), key=lambda m: m.id_account)
  aliases = list()

  for acc_key, acc in all_db_accounts.items():
    similar = account_book._uf_match.find_comp(acc_key)
    db_sim = {(alias.number, alias.name) for alias in db_aliases.get(acc.id, [])}
    missing = similar.difference(db_sim).difference({acc_key})
    aliases.extend([AccountAlias(number=e[0], name=e[1], id_account=acc.id) for e in missing])

  sess.bulk_save_objects(aliases)
  sess.commit()

  return all_db_accounts


def import_belfius_csv(dirname, sess):
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
      custom_id=t.identifier,
      id_source=db_accounts[t.source.identifier].id,
      id_dest=db_accounts[t.dest.identifier].id,
      when=t.when,
      metadata_=make_metadata_serializable(t.metadata),
      amount=t.amount,
      id_currency=[c for c in currencies if t.currency == c.short_name][0].id,
      id_category=None)
    )
    
  save(transacs, sess=sess)



########## MASTERCARD ###########
def check_existing_mastercard_accounts(account_names):
  to_create, all_accounts = set(), dict()
  for account_name in account_names:
    accounts = Account.accounts_by_name(account_name)
    if len(accounts) > 1:
      raise ValueError("several candidates account for a mastercard accounts")
    elif len(accounts) == 0:
      to_create.add(account_name)
    else:
      all_accounts[account_name] = accounts[0]
  return to_create, all_accounts


def make_mscard_metadata(t):
  toisoformat = lambda v: v.isoformat()
  serializer = AsDictSerializer(
    "country_code", "country_or_site", "rate_to_final", "original_currency", 
    closing_date=toisoformat, debit_date=toisoformat, value_date=toisoformat,
    original_amount=(lambda v: None if v is None else str(v)),
  )
  return serializer.serialize(t)


def get_mastercard_preview(dirname):
  _, transactions, account_names, account2currency = parse_folder(dirname)
  to_create, all_accounts = check_existing_mastercard_accounts(account_names)
  logging.getLogger('banking').info("found {} transaction(s) in pdf file(s)".format(len(transactions)))

  currencies = {c.short_name: c for c in Currency.query.all()}
  for t in transactions:
    account_name = t["account"]
    t["account_name"] = account_name
    t["account"] = all_accounts[account_name] if account_name not in to_create else None
    t["currency"] = currencies[t["currency"]]
    if "original_currency" in t:
      t["original_currency"] = currencies[t["original_currency"]]

  toisoformat = lambda v: v.isoformat()
  serializer = AsDictSerializer(
    "account_name", "country_code", "country_or_site", "rate_to_final",
    closing_date=toisoformat, debit_date=toisoformat,
    when=toisoformat, value_date=toisoformat, amount=str, 
    original_amount=(lambda v: None if v is None else str(v)),
    **{k: AsDictSerializer.as_dict_fn() for k in ["original_currency", "account", "currency"]}
  )

  class Struct:
    def __init__(self, **members) -> None:
      self.__dict__.update(**members)

  return [serializer.serialize(Struct(**t)) for t in transactions]


def import_mastercard_pdf(dirname, id_mc_account, sess):
  _, transactions, account_names, account2currency = parse_folder(dirname)
  to_create, all_accounts = check_existing_mastercard_accounts(account_names)

  name2currency = {c.short_name: c for c in Currency.query.all()}
  new_accounts = {name: Account(number=None, name=name, id_currency=name2currency[account2currency[name]].id, initial=0) for name in to_create}
  sess.bulk_save_objects(new_accounts.values(), return_defaults=True)
  sess.commit()

  all_accounts.update(new_accounts)

  new_transactions = list()
  for t in transactions:
    amount = t["amount"]
    id_source, id_dest = id_mc_account, all_accounts[t["account"]].id
    if amount > 0:  # income
      id_source, id_dest = id_dest, id_source
    logging.getLogger().info((make_mscard_metadata(t), id_source, id_dest))
    new_transactions.append(Transaction(
      custom_id=ms_identifier(t),
      id_source=id_source, id_dest=id_dest,
      when=t["when"], amount=amount.copy_abs(),
      metadata_=make_mscard_metadata(t),
      id_currency=name2currency[t["currency"]].id,
      id_category=None,
      data_source="mastercard"
    ))
  
  sess.bulk_save_objects(new_transactions)
  sess.commit()
