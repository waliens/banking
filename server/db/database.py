import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.inspection import inspect

from .build_db import add_currencies, add_tags


def init_db():
    from .models import Account, AccountGroup, AccountAlias
    from .models import Category, Transaction, Currency, Group
    from .models import Base
    database_path = "sqlite:///" + os.getenv("DB_FILE")
    logging.getLogger().debug("connecting to database at '{}' (db file exists? {})".format(database_path, os.path.exists(os.getenv('DB_FILE'))))
    engine = create_engine(database_path)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    Base.query = db_session.query_property()
    if not inspect(engine).has_table(Account.__tablename__):
        logging.getLogger().warn("/!\\ Database does not seem to exist. Create an new one /!\\")
        Base.metadata.create_all(bind=engine)
        add_tags(sess=db_session)
        add_currencies(sess=db_session)
    return db_session, engine
