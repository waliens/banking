import json
import os
import tempfile

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask.wrappers import Response
from flask_cors import CORS

from db.database import init_db
from db.models import Group, Transaction, Account
from data_import import import_beflius_csv

# load environment
load_dotenv()

# create app
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# cors
CORS(app, resources={r"/*": {"origins": "*"}})

# initialize database
Session = init_db()

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


@app.route("/account/<int:id_account>/transactions", methods=["GET"])
def account_transactions(id_account):
    from sqlalchemy import or_
    start = request.args.get("start", type=int, default=0)
    count = request.args.get("count", type=int, default=50)
    transactions = Transaction.query.filter(or_(Transaction.id_dest == id_account, Transaction.id_source == id_account))[start:(start+count)]
    return jsonify([t.as_dict() for t in transactions])


@app.route("/account/groups", methods=["GET"])
def account_groups():
    groups = Group.query.all()
    return jsonify([g.as_dict() for g in groups])

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
            import_beflius_csv(dirname, Session)
        else:
            return Response({"error": "unsupported format", "status": 401})

    return jsonify({"status": "ok"})
