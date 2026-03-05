import inspect
import threading
from contextlib import contextmanager

from sqlalchemy import TEXT, BigInteger, Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import QueuePool

from mfinder import DB_URL, LOGGER

BASE = declarative_base()


class Broadcast(BASE):
    __tablename__ = "broadcast"
    user_id = Column(BigInteger, primary_key=True)
    user_name = Column(TEXT)

    def __init__(self, user_id, user_name):
        self.user_id = user_id
        self.user_name = user_name


def start() -> scoped_session:
    engine = create_engine(
        DB_URL,
        client_encoding="utf8",
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=50,
        pool_timeout=10,
        pool_recycle=1800,
        pool_pre_ping=True,
        pool_use_lifo=True,
    )
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


SESSION = start()
INSERTION_LOCK = threading.RLock()


@contextmanager
def session_scope():
    try:
        yield SESSION
        SESSION.commit()
    except Exception as e:
        SESSION.rollback()
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_code.co_name if caller_frame else "unknown"
        LOGGER.error(
            "Database error occurred in function '%s': %s", caller_name, str(e)
        )
        raise
    finally:
        SESSION.close()


async def add_user(user_id, user_name):
    with INSERTION_LOCK:
        try:
            with session_scope() as session:
                usr = session.query(Broadcast).filter_by(user_id=user_id).first()
                if usr:
                    return False
                usr = Broadcast(user_id=user_id, user_name=user_name)
                session.add(usr)
                return True
        except Exception as e:
            LOGGER.error("Error adding user: %s", str(e))
            return False


async def is_user(user_id):
    with INSERTION_LOCK:
        try:
            with session_scope() as session:
                usr = session.query(Broadcast).filter_by(user_id=user_id).first()
                return usr.user_id if usr else False
        except Exception as e:
            LOGGER.error("Error checking user: %s", str(e))
            return False


async def get_users():
    try:
        with session_scope() as session:
            users = session.query(Broadcast.user_id).order_by(Broadcast.user_id)
            return [user[0] for user in users.all()]
    except Exception as e:
        LOGGER.error("Error getting users: %s", str(e))
        return []


async def del_user(user_id):
    with INSERTION_LOCK:
        try:
            with session_scope() as session:
                usr = session.query(Broadcast).filter_by(user_id=user_id).first()
                if usr:
                    session.delete(usr)
                    return True
                return False
        except Exception as e:
            LOGGER.error("Error deleting user: %s", str(e))
            return False


async def count_users():
    try:
        with INSERTION_LOCK:
            with session_scope() as session:
                total_count = session.query(Broadcast).count()
                return total_count
    except Exception as e:
        LOGGER.error("Error counting users: %s", str(e))
        return 0


async def clear_users():
    try:
        with INSERTION_LOCK:
            with session_scope() as session:
                session.query(Broadcast).delete()
    except Exception as e:
        LOGGER.warning("Error occurred while clearing users: %s", str(e))
