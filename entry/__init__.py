import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from db.models import Base

cwd = os.path.dirname(os.path.dirname(__file__))


def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('PRAGMA journal_mode = MEMORY')


engine = create_engine(f'sqlite:///{cwd}/db/database.db', echo=False, future=True)
autocommit_engine = engine.execution_options(isolation_level="AUTOCOMMIT")

Session = sessionmaker(autocommit_engine)
Base.metadata.create_all(autocommit_engine)
event.listen(autocommit_engine, 'connect', _fk_pragma_on_connect)
