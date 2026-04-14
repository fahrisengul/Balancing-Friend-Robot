import sqlite3
from contextlib import contextmanager

DB_PATH = "poddle.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()
