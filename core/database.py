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
            year INTEGER,
            popularity INTEGER,
            duration INTEGER,
            preview_url TEXT,
            preview_path TEXT,
            deezer_id INTEGER UNIQUE
        )
    """)
    conn.commit()
    conn.close()


def _insert_tracks(tracks: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for track in tracks:
        # Appel supplémentaire pour genre et year
        album_id = track["album"]["id"]
        album_data = requests.get(f"https://api.deezer.com/album/{album_id}").json()
        genre = album_data["genres"]["data"][0]["name"] if album_data["genres"]["data"] else None
        year = int(album_data["release_date"][:4]) if "release_date" in album_data else None
        popularity = track.get("rank", None)

        cursor.execute("""
            INSERT OR IGNORE INTO tracks (deezer_id, title, artist, album, genre, year, popularity, duration, preview_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            track["id"],
            track["title"],
            track["artist"]["name"],
            track["album"]["title"],
            genre,
            year,
            popularity,
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

def import_charts(nb_tracks: int):
    response = requests.get(f"https://api.deezer.com/chart/0/tracks?limit={nb_tracks}")
    _insert_tracks(response.json()["data"])

def import_by_artist(artist_id: int, nb_tracks: int):
    response = requests.get(f"https://api.deezer.com/artist/{artist_id}/top?limit={nb_tracks}")
    _insert_tracks(response.json()["data"])


def get_tracks(nb_tracks: int, genre: str = None, artist: str = None) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT * FROM tracks WHERE preview_path IS NOT NULL"
    params = []

    # Filtres optionnels
    conditions = []
    if genre:
        conditions.append("genre = ?")
        params.append(genre)
    if artist:
        conditions.append("artist = ?")
        params.append(artist)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY RANDOM() LIMIT ?"
    params.append(nb_tracks)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def download_preview(url: str, track_id: int) -> str | None:
    response = requests.get(url)
    if response.status_code != 200 or len(response.content) < 1000:
        print(f"Skipping {track_id} - bad response")
        return None
    preview_path = BASE_DIR / "data" / "music" / f"{track_id}.mp3"
    with open(preview_path, "wb") as f:
        f.write(response.content)

    # Mettre à jour la base
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tracks SET preview_path = ? WHERE deezer_id = ?",
                   (str(preview_path), track_id))
    conn.commit()
    conn.close()
    return str(preview_path)

    return str(preview_path)

def download_all_previews():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT deezer_id, preview_url FROM tracks WHERE preview_path IS NULL")
    rows = cursor.fetchall()
    conn.close()

    for deezer_id, preview_url in rows:
        if preview_url:
            path = download_preview(preview_url, deezer_id)
            print(f"Downloaded {deezer_id}")


def clean_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT deezer_id, preview_path FROM tracks WHERE preview_path IS NOT NULL")
    rows = cursor.fetchall()

    cleaned = 0
    for deezer_id, preview_path in rows:
        path = Path(preview_path)
        if not path.exists() or path.stat().st_size < 1000:  # fichier manquant ou trop petit
            cursor.execute("UPDATE tracks SET preview_path = NULL WHERE deezer_id = ?", (deezer_id,))
            cleaned += 1
            print(f"Cleaned: {deezer_id}")

    conn.commit()
    conn.close()
    print(f"Nettoyé {cleaned} entrées")