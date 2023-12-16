from decimal import getcontext, setcontext
import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import insert
from alembic.config import Config
from alembic import command

from db.db_env import get_db_url

from .util import save


def add_currencies(sess=None):
    from .models import Currency
    stmt = insert(Currency).values([
        {"symbol":"€", "short_name":"EUR", "long_name":"Euro"},
        {"symbol":"$", "short_name":"USD", "long_name":"US Dollar"},
        {"symbol":"£", "short_name":"GBP", "long_name":"GB Pounds"}
    ])
    sess.execute(stmt)


def add_tags(sess=None):
    from .models import Category
    from parsing.tags import TagTree
    tree = TagTree.tree_from_file("parsing")
    import numpy as np 
    v, c = np.unique([t.identifier for t in tree._tags.values()], return_counts=True)
    if np.any(c > 1):
        raise ValueError("duplicate tags identifiers")
   
    stmt = insert(Category).values([{
        "id": t.identifier, 
        "name": t.name, 
        "id_parent": t.parent_id, 
        "color": t.color, 
        "icon": t.icon
    } for _, t in tree._tags.items()])
    sess.execute(stmt)


def add_default_user(sess=None):
    from .models import User
    stmt = insert(User).values(
        username="root",
        password=User.hash_password_string("root")
    )
    sess.execute(stmt)
    

def init_db():
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
    alembic_cfg = Config("/app/alembic.ini")
    command.upgrade(alembic_cfg, "head")

    return db_session, engine
