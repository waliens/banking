import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def init_db():
    from .models import Account, AccountGroup, AccountEquivalence
    from .models import Category, Transaction, Currency, Group
    from .models import Base
    engine = create_engine("sqlite:///" + os.getenv("DB_FILE"))
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    Base.query = db_session.query_property()
    Base.metadata.create_all(bind=engine)
    return db_session
