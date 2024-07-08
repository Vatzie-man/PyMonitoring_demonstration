from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from PyMonitoring.settings._pym_settings import data_base

DATABASE_URL = data_base["control_py_monitoring_db"]


class Base(DeclarativeBase):
    pass


class DBItem(Base):
    __tablename__ = "options"
    option = Column(String, primary_key=True)
    state = Column(String)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def db_query():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
