from sqlalchemy import create_engine, MetaData
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import relation

import sqlalchemy as sa

import webapp.exceptions

CONVENTION = {
    "ix": 'ix_%(table_name)s_%(column_0_label)s',
    # Checks are currently buggy and prevent us from naming them correctly
    # "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
    "uq": "%(table_name)s_%(column_0_name)s_key",
}


BASE = declarative_base(metadata=MetaData(naming_convention=CONVENTION))

def create_tables(db_url, debug=False):
    """ Create the tables in the database using the information from the
    url obtained.
    :arg db_url, URL used to connect to the database. The URL contains
        information with regards to the database engine, the host to
        connect to, the user and password and the database name.
          ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg debug, a boolean specifying whether we should have the verbose
        output of sqlalchemy or not.
    :return a session that can be used to query the database.
    """

    if db_url.startswith('postgres'):
        engine = create_engine(db_url, echo=debug, client_encoding='utf8')
    else:
        engine = create_engine(db_url, echo=debug)

    BASE.metadata.create_all(engine)
    if db_url.startswith('sqlite:'):
        # Ignore the warning about con_record
        # pylint: disable=unused-argument
        def _fk_pragma_on_connect(dbapi_con, _):  # pragma: no cover
            ''' Tries to enforce referential constraints on sqlite. '''
            dbapi_con.execute('pragma foreign_keys=ON')
        sa.event.listen(engine, 'connect', _fk_pragma_on_connect)
    scopedsession = scoped_session(sessionmaker(bind=engine))
    BASE.metadata.bind = scopedsession
    return scopedsession


class Conversion(BASE):
    ''' Table to store information about the conversation ids '''

    __tablename__ = 'conversion'

    id = sa.Column(sa.Integer, primary_key=True)
    uid = sa.Column(sa.String(32), unique=True, nullable=False)
    secure_filename = sa.Column(sa.Text, nullable=False)
