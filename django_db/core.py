import contextlib
import sqlite3
from PyMonitoring.settings._pym_settings import data_base
db_path = data_base['primary_db']


@contextlib.contextmanager
def connect():
    with sqlite3.connect(db_path) as conn:
        yield conn.cursor()
