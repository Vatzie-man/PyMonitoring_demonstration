# TODO -> async

from typing import List
from PyMonitoring.gui_options_db.core import DBItem, SessionLocal, unsuccess_wrapper
db = SessionLocal()


def get_options() -> List[DBItem]:
    return db.query(DBItem).all()


def get_option_filter(key) -> List[DBItem]:
    return db.query(DBItem).filter(DBItem.option.in_([key])).all()


@unsuccess_wrapper
def add_item(option_key: str, state_value: str, db=SessionLocal()):
    new_item = DBItem(option=option_key, state=state_value)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    db.close()
    return new_item


@unsuccess_wrapper
def update_item(option_key: str, state_value: str):
    db = SessionLocal()
    db_item = db.query(DBItem).filter(DBItem.option == option_key).first()
    if db_item is None:
        return None
    db_item.state = state_value
    db.commit()
    db.refresh(db_item)
    return db_item


@unsuccess_wrapper
def delete_item(option_key: str):
    db = SessionLocal()
    db_item = db.query(DBItem).filter(DBItem.option == option_key).first()
    if db_item is None:
        return None
    db.delete(db_item)
    db.commit()
    return db_item
