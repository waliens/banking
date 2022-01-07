import json
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from .models import Base, Category, Account, Group, Transaction, Currency, AccountAlias, AccountGroup
from impl.belfius import BelfiusParserOrchestrator
from parsing import TagTree
from .util import save, make_metadata_serializable


Session = sessionmaker()


def add_currencies(sess=None):
    save([
        Currency(symbol="€", short_name="EUR", long_name="Euro"),
        Currency(symbol="$", short_name="USD", long_name="US Dollar")
    ], sess=sess)


def add_tags(sess=None):
    tree = TagTree.tree_from_file("parsing")
    save([Category(id=t.identifier, name=t.name, id_parent=t.parent_id, color=t.color, income=t.income, default=t.default) for k, t in tree._tags.items()], sess=sess)


def add_accounts_and_transactions():
    path = "./personal"
    orchestrator = BelfiusParserOrchestrator([])
    groups = orchestrator.read(path, add_env_group=True)
    model_map = dict()
    session = Session()
    accounts = list()
    id_default_currency = Currency.short_name_to_id("EUR")
    for group in groups:
        for account in group.accounts:
            print(account.identifier)
            # by default, EUR
            base_account = Account(number=account.number, name=account.name, initial=account.initial, id_currency=id_default_currency)
            save(base_account, sess=session)
            model_map[account.identifier] = base_account

            for alternate in group.account_book._uf_match.find_comp(account.identifier):
                if alternate == account.identifier:
                    continue
                accounts.append(AccountAlias(number=alternate[0], name=alternate[1], id_account=base_account.id))
    save(accounts, sess=session)

    group_model = Group(name=groups[0].name, description="")
    save(group_model, sess=session)

    for account in groups[0].accounts:
        save(AccountGroup(id_group=group_model.id, id_account=model_map[account.identifier].id))

    with open("personal/saved_tags.json", "r", encoding="utf8") as file:
        tags =json.load(file)

    # transactions
    transacs = list()
    for t in groups[0].transaction_book:
        transacs.append(Transaction(
            id=t.identifier,
            id_source=model_map[t.source.identifier].id,
            id_dest=model_map[t.dest.identifier].id,
            when=t.when,
            metadata_=make_metadata_serializable(t.metadata),
            amount=t.amount,
            id_currency=1 if t.currency == "EUR" else 2,
            id_category=tags.get(t.identifier, None)))
    save(transacs, sess=session)


def main():
    load_dotenv()
    engine = create_engine("sqlite:///" + os.getenv("DB_FILE"))
    if not database_exists(engine.url):
        create_database(engine.url)
    else:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
    add_tags()
    add_currencies()
    add_accounts_and_transactions()


if __name__ == "__main__":
    main()