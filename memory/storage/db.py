from contextlib import contextmanager
from pathlib import Path
import sqlite3

# Bu dosya: Robot_Sim/memory/storage/db.py
# Gerçek DB: Robot_Sim/memory/poddle.db
MEMORY_DIR = Path(__file__).resolve().parents[1]
DB_PATH = MEMORY_DIR / "poddle.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()
