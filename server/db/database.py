from decimal import getcontext, setcontext
import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.inspection import inspect
from alembic.config import Config
from alembic import command

from db.db_env import get_db_url

from .util import save


def add_currencies(sess=None):
    from .models import Currency
    save([
        Currency(symbol="€", short_name="EUR", long_name="Euro"),
        Currency(symbol="$", short_name="USD", long_name="US Dollar"),
        Currency(symbol="£", short_name="GBP", long_name="GB Pounds")
    ], sess=sess)


def add_tags(sess=None):
    from .models import Category
    from parsing.tags import TagTree
    tree = TagTree.tree_from_file("parsing")
    import numpy as np 
    v, c = np.unique([t.identifier for t in tree._tags.values()], return_counts=True)
    save([Category(
        id=t.identifier, 
        name=t.name, 
        id_parent=t.parent_id, 
        color=t.color, 
        income=t.income, 
        default=t.default,
        icon=t.icon
    ) for k, t in tree._tags.items()], sess=sess)


def init_db():
    from .models import Account, AccountGroup, AccountAlias
    from .models import Category, Transaction, Currency, Group
    from .models import Base
    database_path = get_db_url()
    logging.getLogger().debug("connecting to database")
    engine = create_engine(database_path)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    Base.query = db_session.query_property()

    # set context
    context = getcontext()
    context.prec = 2
    setcontext(context)

    # create all if necessary
    Base.metadata.create_all(bind=engine)

    is_new_database = not inspect(engine).has_table("alembic_version")
    alembic_cfg = Config("/app/alembic.ini")

    if is_new_database:
        command.stamp(alembic_cfg, "head")
        add_tags(sess=db_session)
        add_currencies(sess=db_session)
    else:
        command.upgrade(alembic_cfg, "head")

    return db_session, engine
