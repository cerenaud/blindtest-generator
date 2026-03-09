import sqlite3
from pathlib import Path
from core.audio import BASE_DIR

DB_PATH = BASE_DIR / "data" / "blindtest.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            album TEXT,
            genre TEXT,
            duration INTEGER,
            preview_url TEXT,
            preview_path TEXT,
            deezer_id INTEGER UNIQUE
        )
    """)
    conn.commit()
    conn.close()

init_db()