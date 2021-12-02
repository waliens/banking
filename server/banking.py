import json

from dotenv import load_dotenv
from flask import Flask, jsonify

from db.database import init_db

# load environment
load_dotenv()

# create app
app = Flask(__name__)

# initialize database
Session = init_db()


@app.route("/account/<int:id_account>/transactions")
def account_transactions(id_account):
    from sqlalchemy import or_
    from db.models import Transaction
    print("aaa")
    transactions = Transaction.query.filter(or_(Transaction.id_dest == id_account, Transaction.id_source == id_account))
    return jsonify([t.as_dict() for t in transactions])


@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()