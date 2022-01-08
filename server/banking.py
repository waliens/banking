import json
import os
import tempfile

from decimal import Decimal
from dotenv import load_dotenv
from flask import Flask, jsonify, request, abort
from flask.wrappers import Response
from flask_cors import CORS
from sqlalchemy.orm.scoping import scoped_session

from sqlalchemy.sql.expression import select, func, cast, column, table, update, or_, and_, delete
from sqlalchemy.sql.operators import json_getitem_op
from sqlalchemy.util import immutabledict
from db.database import init_db
from db.models import AccountAlias, AccountGroup, Group, Transaction, Account
from db.data_import import import_belfius_csv
from background.celery_init import make_celery

# load environment
load_dotenv()

# create app
app = Flask(__name__)
app.config.update(
  JSON_AS_ASCII=False,
  CELERY_BROKER_URL='redis://{}:{}'.format(os.environ.get('REDIS_HOST'), os.environ.get('REDIS_PORT')),
  CELERY_RESULT_BACKEND='redis://{}:{}'.format(os.environ.get('REDIS_HOST'), os.environ.get('REDIS_PORT'))
)

celery = make_celery(app)

# cors
CORS(app, resources={r"/*": {"origins": "*"}})

# initialize database
Session, engine = init_db()


import logging
logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def error_response(msg, code=403):
    response = jsonify({'msg': msg})
    response.status = code
    return response


@app.route("/test/background", methods=["GET"])
def test_background():
    result = add_together.delay(25, 26)
    return jsonify({'val': result.wait()})


@app.route("/account/<int:id_account>/transactions", methods=["GET"])
def account_transactions(id_account):
    from sqlalchemy import or_
    start = request.args.get("start", type=int, default=0)
    count = request.args.get("count", type=int, default=50)
    transactions = Transaction.query \
        .filter(or_(Transaction.id_dest == id_account, Transaction.id_source == id_account)) \
        .order_by(Transaction.when.desc())[start:(start+count)]
    return jsonify([t.as_dict() for t in transactions])


@app.route("/account/<int:id_account>", methods=["GET"])
def get_account(id_account):
    account = Account.query.get(id_account)
    if account is None:
        abort(404)
    return jsonify(account.as_dict())


@app.route("/account/<int:id_account>", methods=["PUT"])
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


@app.route('/account/merge', methods=["PUT"])
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
    
    session.commit()
    
    return jsonify(Account.query.get(id_repr).as_dict())


@app.route("/account/groups", methods=["GET"])
def account_groups():
    groups = Group.query.all()
    return jsonify([g.as_dict() for g in groups])


@app.route("/account_group", methods=["POST"])
def create_group():
    session = Session()
    name = request.json.get("name", "").strip()
    desc = request.json.get("description", "")
    accounts = request.json.get("accounts", [])
    if len(name) == 0 or len(accounts) == 0:
        raise ValueError("empty name or accounts")

    grp = Group(name=name, description=desc)
    session.add(grp)
    session.commit()
    accounts = [AccountGroup(id_account=acc["id"], id_group=grp.id) for acc in accounts]
    session.bulk_save_objects(accounts)
    session.commit()

    return jsonify(grp.as_dict())


@app.route("/account_group/<int:id_group>", methods=["GET"])
def get_account_group(id_group):
    group = Group.query.get(id_group)
    if group is None:
        abort(404)
    return jsonify(group.as_dict())    


@app.route("/accounts", methods=["GET"])
def accounts():
    accounts = Account.query.all()
    return jsonify([a.as_dict() for a in accounts])


@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()


@app.route("/", methods=["GET"])
def home():
    return jsonify({"msg": "hello"})


@app.route("/upload_files", methods=["POST"])
def upload_data():
    format = request.args.get("format", type=int, default="belfius")
    print(request.files)

    with tempfile.TemporaryDirectory() as dirname:
        for i, file in enumerate(request.files.values()):
            filepath = os.path.join(dirname, str(i))
            file.save(filepath) 
        
        if format == "belfius":
            with open(os.path.join(dirname, "accounts.json"), "w+", encoding="utf8") as jsonfile:
                json.dump({}, jsonfile)
            import_belfius_csv(dirname, Session())
        else:
            return Response({"error": "unsupported format", "status": 401})

    return jsonify({"status": "ok"})
