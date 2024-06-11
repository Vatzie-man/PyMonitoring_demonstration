from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import functools

DATABASE_URL = "sqlite:///_options.db"


class Base(DeclarativeBase):
    pass


class DBItem(Base):
    __tablename__ = "options"
    option = Column(String, primary_key=True)
    state = Column(String)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def db_query(func):
    @functools.wraps(func)
    def query_db(*args, **kwargs):
        db = SessionLocal()
        try:
            opt = func(db, *args, **kwargs)
        finally:
            db.close()

        return opt

    return query_db


def unsuccess_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # print(f"{func.__name__!r}-> Option: {result.option} State: {result.state}")
        except Exception:
            print(f"Function: {func.__name__!r} operation failed.")
            result = None

        return result

    return wrapper
