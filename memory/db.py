import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

MEMORY_DIR = Path(__file__).resolve().parents[1]
DB_PATH = MEMORY_DIR / "poddle.db"

@contextmanager
def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    SQLite bağlantısı oluşturur.
    Row factory aktif olduğu için sonuçlar dict-benzeri erişilebilir.
    Thread-safe kullanım için check_same_thread=False açıldı.
    """
    final_path = db_path or DB_PATH
    conn = sqlite3.connect(final_path, check_same_thread=False, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Path] = None, schema_path: Optional[Path] = None) -> None:
    """
    schema.sql dosyasını çalıştırarak veritabanını initialize eder.
    """
    final_db_path = db_path or DB_PATH
    final_schema_path = schema_path or SCHEMA_PATH

    if not final_schema_path.exists():
        raise FileNotFoundError(f"Schema bulunamadı: {final_schema_path}")

    schema_sql = final_schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(final_db_path, check_same_thread=False, timeout=5) as conn:
        conn.executescript(schema_sql)
        conn.commit()

    print(">>> DB PATH:", DB_PATH)
