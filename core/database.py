import sqlite3
from pathlib import Path
from core.audio import BASE_DIR
import requests

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

def _insert_tracks(tracks: list): #private function, only call inside database.py
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for track in tracks:
        cursor.execute("""
            INSERT OR IGNORE INTO tracks (deezer_id, title, artist, album, duration, preview_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            track["id"],
            track["title"],
            track["artist"]["name"],
            track["album"]["title"],
            track["duration"],
            track["preview"]
        ))
    conn.commit()
    conn.close()

def search_and_import(query: str, nb_tracks: int):
    response = requests.get(f"https://api.deezer.com/search?q={query}&limit={nb_tracks}")
    _insert_tracks(response.json()["data"])

def import_by_genre(genre_id: int, nb_tracks: int):
    response = requests.get(f"https://api.deezer.com/chart/{genre_id}/tracks?limit={nb_tracks}")
    _insert_tracks(response.json()["data"])