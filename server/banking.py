from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

from db.database import init_db
from db.models import Transaction, Group

# load environment
load_dotenv()



# create app
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# cors
CORS(app, resources={r"/*": {"origins": "*"}})

# initialize database
Session = init_db()


@app.route("/account/<int:id_account>/transactions")
def account_transactions(id_account):
    from sqlalchemy import or_
    start = request.args.get("start", type=int, default=0)
    count = request.args.get("count", type=int, default=50)
    transactions = Transaction.query.filter(or_(Transaction.id_dest == id_account, Transaction.id_source == id_account))[start:(start+count)]
    return jsonify([t.as_dict() for t in transactions])


@app.route("/account/groups")
def account_groups():
    groups = Group.query.all()
    return jsonify([g.as_dict() for g in groups])


@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()

@app.route("/")
def home():
    return jsonify({"msg": "hello"})