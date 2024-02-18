from datetime import date, timedelta
import json
import os
import re
import tempfile
import uuid

from decimal import Decimal

from dotenv import load_dotenv
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

from sqlalchemy import bindparam
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.expression import select, update, or_, and_, delete, func
from sqlalchemy.util import immutabledict

from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, current_user, get_jwt_identity

from db.database import init_db
from db.models import AccountAlias, AccountGroup, Category, Group, MLModelFile, MLModelState, Transaction, Account, TransactionGroup, User, Currency
from db.data_import import FileNotMatchingDataSource, get_mastercard_preview, import_bank_csv, import_mastercard_pdf
from db.transactions import auto_attribute_partial_transaction_to_groups, auto_attribute_transaction_to_groups_by_accounts
from db.util import get_transaction_query, save

from ml.model_train import train_model
from ml.predict import NoValidModelException, TooManyAvailableModelsException, predict_categories, predict_category

from background.celery_init import make_celery
from db.stats import incomes_expenses, per_category, per_category_aggregated
from parsing.date import parse_date

# load environment
load_dotenv()

# create app
app = Flask(__name__)
app.config.update(
  JSON_AS_ASCII=False,
  CELERY_BROKER_URL='redis://{}:{}'.format(os.environ.get('REDIS_HOST'), os.environ.get('REDIS_PORT')),
  CELERY_RESULT_BACKEND='redis://{}:{}'.format(os.environ.get('REDIS_HOST'), os.environ.get('REDIS_PORT')),
  JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY'),
  JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
  JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1)
)

# celery workers
celery = make_celery(app)

# cors
CORS(app, resources={r"/*": {"origins": "*"}})

# initialize database
Session, engine = init_db()

# authentication
jwt = JWTManager(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
  return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
  identity = jwt_data["sub"]
  with Session():
    return User.query.filter_by(id=identity).one_or_none()


import logging
logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

#################### CELERY TASKS #######################
@celery.task
def trigger_model_train(target):
  train_model(trigger_model_train.session, data_source=target)

@celery.task
def delete_invalid_models():
  session = delete_invalid_models.session
  models = MLModelFile.get_models_by_state(MLModelState.INVALID)
  for model in models:
    filepath = os.path.join(os.getenv("MODEL_PATH"), model.filename)
    if os.path.exists(filepath):
      os.remove(filepath)
    model.state = MLModelState.DELETED
  session.commit()
#########################################################

def bool_type(v):
  if isinstance(v, bool):
    return v
  return v.lower() in {"1", "true"}


def bool_or_int_type(v):
  if v.isnumeric():
    return int(v)
  else:
    return bool_type(v)


def date_type(v):
  if isinstance(v, date):
    return v
  return date.fromisoformat(v)


def error_response(msg, code=403):
  response = jsonify({'msg': msg})
  response.status = code
  return response


def basic_success(msg="success", code=200):
  repsonse = jsonify({'msg': msg})
  repsonse.status = code
  return repsonse


@app.route("/login", methods=["POST"])
def login():
  username = request.json.get("username", None)
  password = request.json.get("password", None)

  user = User.query.filter_by(username=username).one_or_none()
  if not user or not user.check_password(password):
    return error_response("wrong username or password", 401)

  # Notice that we are passing in the actual sqlalchemy user object here
  access_token = create_access_token(identity=user)
  refresh_token = create_refresh_token(identity=user)
  return jsonify(access_token=access_token, refresh_token=refresh_token)


@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
  identity = get_jwt_identity()
  session = Session()
  access_token = create_access_token(identity=session.get(User, identity))
  return jsonify(access_token=access_token)


@app.route('/user/current', methods=["GET"])
@jwt_required()
def get_current_user():
  return jsonify(current_user.as_dict())


@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():
  with Session():
    users = User.query.all()
    return jsonify([user.as_dict() for user in users])


@app.route('/user', methods=["POST"])
@jwt_required()
def create_user():
  username = request.json.get("username")
  password = request.json.get("password")

  if username is None or len(username) == 0 or password is None or len(username) == 0:
    return error_response("invalid password or username")

  with Session() as sess:
    user_count = User.query.filter_by(username=username).count()
    if user_count > 0:
      return error_response("username already used")
    new_user = User(username=username, password=User.hash_password_string(password))
    save(new_user, sess)
    return jsonify(new_user.as_dict())


@app.route('/user/<int:id_user>', methods=["PUT"])
@jwt_required()
def update_user(id_user):
  username = request.json.get("username")
  password = request.json.get("password")

  if (username is None or len(username) == 0) and (password is None and len(password) == 0):
    return error_response("no value provided for update")

  with Session() as sess:
    # check new username existence
    user = User.query.filter_by(id=id_user).one_or_none()
    if user is None:
      return error_response("user not found", 404)
    if username is not None and username != user.username:
      user.username = username
    if password is not None:
      user.password = User.hash_password_string(password)
    sess.commit()
    return jsonify(user.as_dict())


@app.route("/account/<int:id_account>/transactions", methods=["GET"])
@jwt_required()
def account_transactions(id_account):
  from sqlalchemy import or_
  start = request.args.get("start", type=int, default=0)
  count = request.args.get("count", type=int, default=50)
  transactions = Transaction.query \
    .filter(
      or_(Transaction.id_dest == id_account, Transaction.id_source == id_account),
      Transaction.id_is_duplicate_of == None
    ) \
    .order_by(Transaction.when.desc())[start:(start+count)]
  return jsonify([t.as_dict() for t in transactions])


@app.route("/transactions", methods=["GET"])
@jwt_required()
def get_transactions():
  # filters
  start = request.args.get("start", type=int, default=0)
  count = request.args.get("count", type=int, default=50)
  order = request.args.get("order", type=str, default="desc")
  sort_by = request.args.get("sort_by", type=str, default=None)
  account = request.args.get("account", type=int, default=None)
  account_to = request.args.get("account_to", type=int, default=None)
  account_from = request.args.get("account_from", type=int, default=None)
  group = request.args.get("group", type=int, default=None)
  group_external_only = request.args.get("group_external_only", type=bool_type, default=False)
  in_group = request.args.get("in_group", type=int, default=1)
  labeled = request.args.get("labeled", type=bool_or_int_type, default=None)
  date_from = request.args.get("date_from", type=date_type, default=None)
  date_to = request.args.get("date_to", type=date_type, default=None)
  amount_from = request.args.get("amount_from", type=Decimal, default=None)
  amount_to = request.args.get("amount_to", type=Decimal, default=None)
  duplicate_only = request.args.get("duplicate_only", type=bool_type, default=False)
  search_query = request.args.get("search_query", type=str, default=None)

  ## conditional content
  # add fields: ml_category (object), ml_proba (float)
  ml_category = request.args.get("ml_category", type=bool_type, default=False)
  # group id needs to be provided, add fields: in_group (bool), contribution_ratio (float)
  group_data = request.args.get("group_data", type=bool_type, default=False)

  if account is not None and group is not None:
    return error_response("cannot set both account and account_group when fetching transactions")
  if sort_by is not None and sort_by not in {'when', 'amount'}:
    return error_response("cannot fetch transactions without categories but with a category id")
  if date_from is not None and date_to is not None and date_from > date_to:
    return error_response("cannot have a date_from after date_to")
  if amount_from is not None and amount_to is not None and amount_from > amount_to:
    return error_response("cannot have a amount_from greater than amount_to")
  if (group_data or group_external_only) and group is None:
    return error_response("group id must be provided if group_data or group_external_only is requested")
  if search_query is not None and len(search_query) < 3:
    return error_response("cannot search for search query of length < 3")

  # not filtering by group
  if in_group == -1:
    in_group = None

  # fetch
  transactions = get_transaction_query(
    search_query=search_query,
    account=account,
    group=group,
    group_external_only=group_external_only,
    in_group=in_group,
    labeled=labeled,
    sort_by=sort_by,
    order=order,
    account_from=account_from,
    account_to=account_to,
    date_from=date_from,
    date_to=date_to,
    amount_from=amount_from,
    amount_to=amount_to,
    duplicate_only=duplicate_only
  )[start:(start+count)]

  to_return = [
    t.as_dict(show_is_duplicate_of=duplicate_only)
    for t in transactions
  ]

  if ml_category:
    categories, probas = predict_categories(transactions)
    for t_dict, c, p in zip(to_return, categories, probas):
      t_dict["ml_category"] = c.as_dict() if c is not None else None
      t_dict["ml_proba"] = p if c is not None else 0

  if group_data:
    transaction_groups = TransactionGroup.query.where(and_(
      TransactionGroup.id_group == group,
      TransactionGroup.id_transaction.in_([t.id for t in transactions])
    )).all()
    tg_map = {tg.id_transaction: tg for tg in transaction_groups}
    for t_dict in to_return:
      if t_dict["id"] in tg_map:
        t_dict["in_group"] = True
        t_dict["contribution_ratio"] = tg_map[t_dict["id"]].contribution_ratio
      else:
        t_dict["in_group"] = False
        t_dict["contribution_ratio"] = None

  return jsonify(to_return)


@app.route("/transactions/count", methods=["GET"])
@jwt_required()
def get_transactions_count():
  account = request.args.get("account", type=int, default=None)
  account_to = request.args.get("account_to", type=int, default=None)
  account_from = request.args.get("account_from", type=int, default=None)
  group = request.args.get("group", type=int, default=None)
  group_external_only = request.args.get("group_external_only", type=bool_type, default=False)
  in_group = request.args.get("in_group", type=int, default=1)
  labeled = request.args.get("labeled", type=bool_or_int_type, default=None)
  date_from = request.args.get("date_from", type=date_type, default=None)
  date_to = request.args.get("date_to", type=date_type, default=None)
  amount_from = request.args.get("amount_from", type=Decimal, default=None)
  amount_to = request.args.get("amount_to", type=Decimal, default=None)
  duplicate_only = request.args.get("duplicate_only", type=bool_type, default=False)
  search_query = request.args.get("search_query", type=str, default=None)

  if account is not None and group is not None:
    return error_response("cannot set both account and account_group when fetching transactions")
  if date_from is not None and date_to is not None and date_from > date_to:
    return error_response("cannot have a date from after date_to")
  if amount_from is not None and amount_to is not None and amount_from > amount_to:
    return error_response("cannot have a amount_from greater than amount_to")
  if group_external_only and group is None:
    return error_response("group id must be provided if group_data or group_external_only is requested")
  if search_query is not None and len(search_query) < 3:
    return error_response("cannot search for search query of length < 3")
  
  # not filtering by group
  if in_group == -1:
    in_group = None

  # fetch
  query = get_transaction_query(
    search_query=search_query,
    account=account,
    group=group,
    group_external_only=group_external_only,
    in_group=in_group,
    labeled=labeled,
    account_from=account_from,
    account_to=account_to,
    date_from=date_from,
    date_to=date_to,
    amount_from=amount_from,
    amount_to=amount_to,
    duplicate_only=duplicate_only
  )
  return jsonify({'count': query.count() })


@app.route("/transactions/tag", methods=["PUT"])
@jwt_required()
def tag_transactions():
  sess = Session()
  transaction_data = [{"id": o["id_transaction"], "id_category": o["id_category"]} for o in request.json.get("categories", [])]
  sess.execute(update(Transaction), transaction_data, execution_options={"synchronize_session": False})
  sess.commit()
  return basic_success()


@app.route("/transaction/<int:id_transaction>/category/<int:id_category>", methods=["PUT"])
@jwt_required()
def set_transaction_category(id_transaction, id_category):
  session = Session()
  session.execute(update(Transaction).where(Transaction.id==id_transaction).values(id_category=id_category))
  session.commit()
  return jsonify(Transaction.query.get(id_transaction).as_dict())


@app.route("/transaction/<int:id_transaction>/category/infer", methods=["GET"])
@jwt_required()
def ml_infer_category(id_transaction):
  transaction = Transaction.query.get(id_transaction)
  if transaction is None:
    abort(404)
  try:
    category, proba = predict_category(transaction)
    return jsonify({"category": category.as_dict(), "proba": proba})
  except NoValidModelException:
    trigger_model_train.delay(transaction.data_source)
    return error_response("no valid model ready (retry later)", code=400)
  except TooManyAvailableModelsException("too many available model for prediction"):
    return error_response("too many models available for prediction", code=500)


@app.route("/transaction/<int:id_transaction>", methods=["GET"])
@jwt_required()
def get_transaction(id_transaction):
  session = Session()
  transaction = session.get(Transaction, id_transaction)
  if transaction is None:
    return error_response("transaction not found", 404)
  return jsonify(transaction.as_dict())


@app.route("/transaction/<int:id_transaction>/account_groups", methods=["GET"])
@jwt_required()
def get_account_groups_of_transactions(id_transaction):
  session = Session()
  groups = session.execute(select(TransactionGroup.id_group).where(TransactionGroup.id_transaction == id_transaction)).all()
  return jsonify([g.id_group for g in groups])


@app.route("/transaction", methods=["POST"])
@jwt_required()
def create_manual_transaction():
  id_source = request.json.get("id_source", None)
  id_dest = request.json.get("id_dest", None)
  date_when = request.json.get("when", None)
  metadata_ = request.json.get("metadata_", dict())
  amount = request.json.get("amount", None)
  id_currency = request.json.get("id_currency", None)
  id_category = request.json.get("id_category", None)
  id_group = request.json.get("id_group", None)

  if date_when is None:
    return error_response("'when' is empty, should be set to a date")
  else:
    date_when = parse_date(date_when)
  if amount is None:
    return error_response("'amount' is empty, should be set to a decimal number")
  if id_currency is None:
    return error_response("'currency' is empty, should be set to the id of the currency")

  session = Session()
  with session.begin():
    if amount < 0:
      id_dest, id_source = id_source, id_dest
    transaction = Transaction(
      custom_id=uuid.uuid4(),
      id_source=id_source,
      id_dest=id_dest,
      when=date_when,
      metadata_=metadata_,
      amount=abs(Decimal(amount)),
      id_currency=id_currency,
      id_category=id_category,
      data_source="manual",
      id_is_duplicate_of=None
    )
    session.add(transaction)
    session.flush()
    session.refresh(transaction)

    if id_group is not None:
      session.add(TransactionGroup(
        id_group=id_group,
        id_transaction=transaction.id,
        contribution_ratio=1
      ))

    return jsonify(transaction.as_dict())


@app.route("/transaction/<int:id_transaction>", methods=["PUT"])
@jwt_required()
def edit_manual_transaction(id_transaction):
  session = Session()
  with session.begin():
    transaction = session.get(Transaction, id_transaction)
    if transaction is None:
      error_response("transaction not found", 404)
    if transaction.data_source != "manual":
      return error_response("cannot edit a non-manual transaction")

    # update fields
    if "when" in request.json:
      when = request.json.get("when")
      if when is None:
        return error_response("when empty, should be set to a date")
      transaction.when = parse_date(when)
    if "metadata_" in request.json:
      transaction.metadata_ = request.json.get("metadata_")
    if "id_currency" in request.json:
      id_currency = request.json.get("id_currency")
      if id_currency is None:
        return error_response("'currency' is empty, should be set to the id of the currency")
      transaction.id_currency = id_currency
    if "id_category" in request.json:
      transaction.id_category = request.json.get("id_category")
    new_source, new_dest = transaction.id_source, transaction.id_dest
    if "id_dest" in request.json:
      new_dest = request.json.get("id_dest")
    if "id_source" in request.json:
      new_source = request.json.get("id_source")
    if "amount" in request.json:
      amount = request.json.get("amount")
      if amount is None:
        return error_response("'amount' is empty, should be set to a decimal number")
      if amount < 0:
        new_source, new_dest = new_dest, new_source
      transaction.amount = abs(Decimal(amount))
    transaction.id_dest = new_dest
    transaction.id_source = new_source
    return jsonify(transaction.as_dict())


@app.route("/transaction/<int:id_transaction>", methods=["DELETE"])
@jwt_required()
def delete_manual_transaction(id_transaction):
  session = Session()
  with session.begin():
    transaction = session.get(Transaction, id_transaction)
    if transaction is None:
      error_response("transaction not found", 404)
    if transaction.data_source != "manual":
      return error_response("cannot delete a non-manual transaction")
    # check if transaction group
    group_counts = session.scalar(
      select(func.count())
        .select_from(TransactionGroup)
        .where(TransactionGroup.id_transaction == id_transaction)
    )
    if group_counts > 0:
      return error_response("cannot delete the transaction because it is associated to a group")
    session.delete(transaction)
    session.commit()


@app.route("/transaction/<int:id_transaction>/duplicate_of/candidates", methods=["GET"])
@jwt_required()
def get_candidate_duplicates(id_transaction: int):
  days_offset = request.args.get("days", default=7, type=int)
  session = Session()
  with session.begin():
    transaction = session.get(Transaction, id_transaction)
    if transaction is None:
      error_response("transaction not found", 404)
    after_date = transaction.when - timedelta(days=days_offset)
    before_date = transaction.when + timedelta(days=days_offset)
    where = [
      Transaction.amount == transaction.amount,
      Transaction.when < before_date,
      Transaction.when > after_date,
      Transaction.id != transaction.id, # the query transaction cannot be a candidate
      Transaction.id_is_duplicate_of == None  # an existing duplicate cannot be a candidate
    ]
    if transaction.id_source != None:
      where.append(or_(Transaction.id_source == None, Transaction.id_source == transaction.id_source))
    if transaction.id_dest != None:
      where.append(or_(Transaction.id_dest == None, Transaction.id_dest == transaction.id_dest))
    candidates = session.execute(select(Transaction).where(*where)).unique().all()
    return jsonify([t[0].as_dict() for t in candidates])


@app.route("/transaction/<int:id_duplicate>/duplicate_of/<int:id_parent>", methods=["PUT"])
@jwt_required()
def set_duplicate_of(id_duplicate: int, id_parent: int):
  session = Session()
  with session.begin():
    parent = session.get(Transaction, id_parent)
    if parent is None:
      return error_response("parent transaction not found", 404)
    if parent.id_is_duplicate_of is not None:
      return error_response("requested parent is already a duplicate", 403)
    duplicate = session.get(Transaction, id_duplicate)
    if duplicate is None:
      return error_response("duplicate transaction not found", 404)
    duplicate.id_is_duplicate_of = id_parent
    session.flush()
    return basic_success()


@app.route("/transaction/<int:id_transaction>/duplicate_of", methods=["DELETE", "PUT"])
@jwt_required()
def unset_duplicate_of(id_transaction):
  session = Session()
  with session.begin():
    transaction = session.get(Transaction, id_transaction)
    if transaction is None:
      error_response("transaction not found", 404)
    transaction.id_is_duplicate_of = None
    session.flush()
    return basic_success()


@app.route("/account/<int:id_account>", methods=["GET"])
@jwt_required()
def get_account(id_account):
  account = Account.query.get(id_account)
  if account is None:
    abort(404)
  return jsonify(account.as_dict())


@app.route("/account/<int:id_account>", methods=["PUT"])
@jwt_required()
def update_account(id_account):
  initial = request.json.get("initial")
  id_representative = request.json.get("id_representative")

  session = Session()
  account = Account.query.get(id_account)
  if account is None:
    abort(404)

  if initial is not None:
    account.initial = Decimal(initial)

  if id_representative is not None:
    alias = AccountAlias.query.get(id_representative)
    if alias is None:
      session.rollback()
      abort(error_response("alias does not exist", code=403))
    alias.name, account.name = account.name, alias.name
    alias.number, account.number = account.number, alias.number

  session.commit()
  return jsonify(account.as_dict())


@app.route("/account/<int:id_account>/alias", methods=["POST"])
@jwt_required()
def add_alias(id_account):
  name = request.json.get("name", None)
  number = request.json.get("number", None)
  session = Session()
  account = Account.query.get(id_account)
  all_aliases = [(account.name, account.number), *[(alias.name, alias.number) for alias in account.aliases]]
  matching = [a for a in all_aliases if a == (name, number)]
  app.logger.info(all_aliases)
  app.logger.info((name, number))
  if len(matching) > 0:
    return error_response("cannot add this alias, already exists")
  new_alias = AccountAlias(name=name, number=number, id_account=id_account)
  session.add(new_alias)
  session.commit()
  return new_alias.as_dict()


@app.route('/account/merge', methods=["PUT"])
@jwt_required()
def merge_accounts():
  id_alias = request.json.get("id_alias")
  id_repr = request.json.get("id_repr")

  if id_alias == id_repr:
    abort(error_response("Cannot merge an account with itself."))

  session = Session()
  alias = Account.query.get(id_alias)
  repr = Account.query.get(id_repr)

  if alias is None or repr is None:
    abort(error_response("Alias or repr account does not exist."))

  transactions = Transaction.query.filter(or_(
    and_(Transaction.id_source == repr.id, Transaction.id_dest == alias.id),
    and_(Transaction.id_source == alias.id, Transaction.id_dest == repr.id))).all()

  if len(transactions) > 0:
    abort(error_response("There exists at least one transaction between the two accounts to merge. Therefore, they cannot be merged."))

  # alias account aliases should be switch to repr's
  session.execute(update(AccountAlias).where(AccountAlias.id_account==alias.id).values(id_account=repr.id))

  # transactions referencing the alias account should now be referencing the repr account
  session.execute(update(Transaction).where(Transaction.id_source==alias.id).values(id_source=repr.id))
  session.execute(update(Transaction).where(Transaction.id_dest==alias.id).values(id_dest=repr.id))

  # account groups referencing the alias account should now be referencing the repr account
  # (be careful about unique constraint if both alias and repr are in a group)
  session.execute(update(AccountGroup).where(and_(
    AccountGroup.id_account==alias.id,
    AccountGroup.id_group.not_in(select(AccountGroup.id_group).where(AccountGroup.id_account==repr.id))
  )).values(id_account=repr.id), execution_options=immutabledict({"synchronize_session": 'fetch'}))
  session.execute(delete(AccountGroup).where(AccountGroup.id_account==alias.id))

  # alias account should be removed and added as an alias
  session.add(AccountAlias(name=alias.name, number=alias.number, id_account=repr.id))
  session.delete(alias)

  # invalidate models
  session.execute(MLModelFile.invalidate_models_stmt())
  delete_invalid_models.delay()

  session.commit()

  return jsonify(Account.query.get(id_repr).as_dict())


@app.route("/account/groups", methods=["GET"])
@jwt_required()
def account_groups():
  groups = Group.query.all()
  return jsonify([g.as_dict() for g in groups])


@app.route("/account_group", methods=["POST"])
@jwt_required()
def create_group():
  name = request.json.get("name", "").strip()
  desc = request.json.get("description", "")
  account_groups = request.json.get("account_groups", [])
  if len(name) == 0 or len(account_groups) == 0:
    raise ValueError("empty name or accounts")
  if any([not 0 < float(ag["contribution_ratio"]) <= 1 for ag in account_groups]):
    return error_response("one or several invalid contribution ratio")
  if any([ag.get("id_account") is None for ag in account_groups]):
    return error_response("one or several missing account id for account group")

  session = Session()
  with session.begin():
    grp = Group(name=name, description=desc)
    session.add(grp)
    session.flush()
    ag_models = [
      AccountGroup(
        id_account=ag["id_account"],
        id_group=grp.id,
        contribution_ratio=ag.get("contribution_ratio", 1)
      )
      for ag in account_groups
    ]
    session.add_all(ag_models)
    session.commit()

  auto_attribute_transaction_to_groups_by_accounts(session, {ag['id_account'] for ag in account_groups})

  return jsonify(grp.as_dict())

@app.route("/account_group/<int:id_group>", methods=["PUT"])
@jwt_required()
def update_group(id_group):
  session = Session()
  with session.begin():
    group = Group.query.get(id_group)
    group.name = request.json.get("name", group.name)
    if group.name is not None:
      group.name = group.name.strip()
    group.description = request.json.get("description", group.description)
    if group.description is not None:
      group.description = group.description.strip()
    session.flush()
    # TODO evalute diff for auto-update of TransactionGroup
    session.execute(delete(AccountGroup).where(AccountGroup.id_group==id_group))
    session.bulk_save_objects([AccountGroup(
      id_account=ag["id_account"],
      id_group=id_group,
      contribution_ratio=ag.get("contribution_ratio", 1)
    ) for ag in request.json.get('account_groups')])
    session.commit()
  return jsonify(group.as_dict())


@app.route("/account_group/<int:id_group>", methods=["GET"])
@jwt_required()
def get_account_group(id_group):
  group = Group.query.get(id_group)
  if group is None:
    abort(404)
  return jsonify(group.as_dict())


@app.route("/account_group/<int:id_group>/transactions", methods=["PUT"])
@jwt_required()
def link_transactions(id_group):
  sess = Session()
  stmt = insert(TransactionGroup).values({
    TransactionGroup.id_group: bindparam('id_group'),
    TransactionGroup.id_transaction: bindparam('id_transaction'),
    TransactionGroup.contribution_ratio: bindparam("ratio")
  }).on_conflict_do_nothing()
  sess.execute(stmt, [
    {'id_group': id_group, "id_transaction": tid, "ratio": 1.0}
    for tid in request.json.get("transactions", [])
  ])
  sess.commit()
  return basic_success()


@app.route("/account_group/<int:id_group>/transactions", methods=["DELETE"])
@jwt_required()
def unlink_transactions(id_group):
  sess = Session()
  stmt = delete(TransactionGroup).where(and_(
    TransactionGroup.id_group == id_group,
    TransactionGroup.id_transaction.in_(request.json.get("transactions", []))
  ))
  sess.execute(stmt)
  sess.commit()
  return basic_success()


@app.route("/account_group/<int:id_group>/stats/incomeexpense")
@jwt_required()
def get_group_income_expense(id_group):
  year = request.args.get("year", type=int, default=None)
  month = request.args.get("month", type=int, default=None)
  session = Session()
  expenses, incomes, currencies = incomes_expenses(session, id_group, year=year, month=month)
  return jsonify({'incomes': incomes, 'expenses': expenses, 'currencies': [c.as_dict() for c in currencies]})


@app.route("/account_group/<int:id_group>/stats/percategory")
@jwt_required()
def get_group_stats_per_category(id_group):
  period_from = request.args.get("period_from", type=date_type, default=None)
  period_to = request.args.get("period_to", type=date_type, default=None)
  level = request.args.get("level", type=int, default=-1)
  unlabeled = request.args.get("unlabeled", type=bool_type, default=True)
  id_category = request.args.get("id_category", type=int, default=None)
  # if omitted, fetch both income and expense
  session = Session()
  if "income_only" in request.args:
    income_only = request.args.get("income_only", type=bool_type)
    buckets = per_category(
      session,
      id_group,
      income_only=income_only,
      period_from=period_from,
      period_to=period_to,
      id_category=id_category,
      include_unlabeled=unlabeled,
      bucket_level=level
    )
  else: 
    buckets = per_category_aggregated(
      session,
      id_group,
      period_from=period_from,
      period_to=period_to,
      id_category=id_category,
      include_unlabeled=unlabeled,
      bucket_level=level
    )    
  return jsonify(buckets[-1] if len(buckets) > 0 else [])


@app.route("/account_group/<int:id_group>/stats/percategorymonthly")
@jwt_required()
def get_group_stats_per_category_monthly(id_group):
  period_from = request.args.get("period_from", type=date_type, default=None)
  period_to = request.args.get("period_to", type=date_type, default=None)
  level = request.args.get("level", type=int, default=-1)
  unlabeled = request.args.get("unlabeled", type=bool_type, default=True)
  id_category = request.args.get("id_category", type=int, default=None)
  income_only = request.args.get("income_only", type=bool_type, default=True)
  session = Session()
  buckets = per_category(
    session,
    id_group,
    income_only=income_only,
    period_from=period_from,
    period_to=period_to,
    id_category=id_category,
    include_unlabeled=unlabeled,
    bucket_level=level,
    period_bucket="month"
  )
  # convert decimals
  for bot_buckets in buckets.values():
    for curr_bucket in bot_buckets:
      curr_bucket["amount"] = float(curr_bucket["amount"])

  return jsonify(buckets)


@app.route("/accounts", methods=["GET"])
@jwt_required()
def accounts():
  accounts = Account.query.all()
  return jsonify([a.as_dict(show_balance=False) for a in accounts])


@app.route("/model/<target>/refresh", methods=["POST"])
@jwt_required()
def refresh_model(target):
  if target not in {'belfius'}:
    return error_response({'msg': 'invalid target'}, code=403)
  session = Session()
  session.execute(MLModelFile.invalidate_models_stmt(target=target))
  session.commit()
  delete_invalid_models.delay()
  trigger_model_train.delay(target)
  return jsonify({'msg': 'retrain triggered'})


@app.route("/models", methods=["GET"])
@jwt_required()
def get_models():
  return jsonify([m.as_dict() for m in MLModelFile.query.all()])


@app.route("/categories", methods=["GET"])
@jwt_required()
def get_categories():
  return jsonify([c.as_dict() for c in Category.query.all()])


@app.route("/category/<int:id_category>", methods=["PUT"])
@jwt_required()
def update_category(id_category):
  session = Session()
  category = Category.query.get(id_category)
  if category is None:
    return error_response("category not found", 404)
  name = request.json.get("name", category.name)
  id_parent = request.json.get("id_parent", category.id_parent)
  color = request.json.get("color", category.color)
  icon = request.json.get("icon", category.icon)

  category.name = name
  category.id_parent = id_parent
  category.color = color
  category.icon = icon

  session.execute(MLModelFile.invalidate_models_stmt())

  session.commit()
  return jsonify(category.as_dict())


@app.route("/category/<int:id_category>", methods=["DELETE"])
@jwt_required()
def delete_category(id_category):
  session = Session()
  category = Category.query.get(id_category)
  session.execute(update(Category).where(Category.id_parent == id_category).values({Category.id_parent: category.id_parent}))
  # TODO check/implement proper ON DELETE SET NULL
  session.execute(update(Transaction).where(Transaction.id_category == id_category).values({Transaction.id_category: None}))
  session.execute(delete(Category).where(Category.id == id_category))
  session.execute(MLModelFile.invalidate_models_stmt())
  session.commit()
  return basic_success()


@app.route("/category", methods=["POST"])
@jwt_required()
def add_category():
  name = request.json.get("name")
  id_parent = request.json.get("id_parent")
  color = request.json.get("color")
  icon = request.json.get("icon")

  if re.match(r"^#[A-Z0-9]{6}$", color, re.IGNORECASE) is None:
    return error_response("invalid color string '{}'".format(color))
  if len(name) < 1:
    return error_response("emptu category name")

  session = Session()
  category = Category(name=name, id_parent=id_parent, color=color, icon=icon)
  session.add(category)
  session.commit()

  return jsonify(category.as_dict())


@app.route("/upload_files", methods=["POST"])
@jwt_required()
def upload_data():
  format = request.args.get("format")
  app.logger.info("file upload with format '{}'".format(format))

  with tempfile.TemporaryDirectory() as dirname:
    for i, file in enumerate(request.files.values()):
      filepath = os.path.join(dirname, str(i))
      file.save(filepath)

    session = Session()
    # actual upload
    if format not in {"belfius", "mastercard_pdf_preview", "mastercard_pdf", "ing"}:
      return error_response("unsupported upload format", 401)

    if format == "mastercard_pdf_preview":
      preview = get_mastercard_preview(dirname, session)
      return jsonify(preview)

    if format == "mastercard_pdf":
      id_mscard_account = request.args.get("id_mscard_account")
      transactions = import_mastercard_pdf(dirname, id_mscard_account, session)
    else: # belfius, ing
      try:
        transactions = import_bank_csv(format, dirname, session)
      except FileNotMatchingDataSource:
        return error_response("file format not matching data source")

      # auto attribute these new transactions to groups that match them
    auto_attribute_partial_transaction_to_groups(session, transactions)
    return jsonify({"status": "ok"})


@app.route("/currencies", methods=["GET"])
@jwt_required()
def get_currencies():
  session = Session()
  currencies = session.execute(select(Currency)).all()
  return jsonify([t[0].as_dict() for t in currencies])


@app.teardown_appcontext
def shutdown_session(exception=None):
  Session.remove()