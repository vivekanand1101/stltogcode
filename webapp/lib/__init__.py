import redis
import json
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from webapp.lib import model

REDIS = None

def set_redis(host, port, dbname):
    """ Set the redis connection with the specified information. """
    global REDIS
    pool = redis.ConnectionPool(host=host, port=port, db=dbname)
    REDIS = redis.StrictRedis(connection_pool=pool)


def create_session(db_url, debug=False, pool_recycle=3600):
    ''' Create the Session object to use to query the database.
    :arg db_url: URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg debug: a boolean specifying whether we should have the verbose
        output of sqlalchemy or not.
    :return a Session that can be used to query the database.
    '''

    if db_url.startswith('postgres'):
        engine = sqlalchemy.create_engine(
            db_url, echo=debug, pool_recycle=pool_recycle,
            client_encoding='utf8')
    else:
        engine = sqlalchemy.create_engine(
            db_url, echo=debug, pool_recycle=pool_recycle)
    scopedsession = scoped_session(sessionmaker(bind=engine))
    model.BASE.metadata.bind = scopedsession
    return scopedsession


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def get_file(session, uid):
    ''' Get the file object, given the uid '''

    return session.query(
        model.Conversion).filter(model.Conversion.uid==uid).first()


def send_to_redis(uid):
    ''' Send the file to redis for file conversion '''

    REDIS.publish(
        'webapp.convert',
        json.dumps({
            'uid': uid,
        })
    )

def trigger_ev_server(uid, json_out):
    ''' Send the file to redis for event source '''

    REDIS.publish(
        'webapp.%s' % uid,
        json_out,
    )
