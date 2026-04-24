import sqlite3
from pathlib import Path
from ai.agents import correct_release_year
from core.audio import BASE_DIR
import requests
import time

DB_PATH = BASE_DIR / "data" / "blindtest.db"

#Create a database to download previews from deezer
# Genre and ID:
# 0 : All
# 132 : Pop
# 116: Rap/ Hip Hop
# 152 : Rock
# 113 : Dance
# 165 : R&B
# 85 : Alternative
# 106 : Electro
# 52 : Chanson française
# 144 : Reggae
# 129 : Jazz
# 464 : Metal
# 169 : Soul & Funk
# 153 : Blues
# 197 : Latino

def init_db():
    """Create a database for the music previews from deezer API.
    """
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
            preview_path TEXT,
            album_cover_url TEXT,
            album_cover_path TEXT,
            deezer_id INTEGER UNIQUE
        )
    """)
    conn.commit()
    conn.close()


def _insert_tracks(
        tracks: list
):
    """Insert tracks into database

    Parameters
    ----------
    tracks : list
        a list of tracks from the deezer API.

    """
    data = {
        "songs": []
    }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for track in tracks:
        # Appel supplémentaire pour genre et year
        album_id = track["album"]["id"]
        album_data = requests.get(f"https://api.deezer.com/album/{album_id}").json()
        album_cover_url = album_data.get("cover_big", None)
        genre = album_data["genres"]["data"][0]["name"] if album_data["genres"]["data"] else None
        year = int(album_data["release_date"][:4]) if "release_date" in album_data else None
        popularity = track.get("rank", None)

        cursor.execute("""
            INSERT OR IGNORE INTO tracks (deezer_id, title, artist, album, genre, year, popularity, duration, album_cover_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)
        """, (
            track["id"],
            track["title_short"],
            track["artist"]["name"],
            track["album"]["title"],
            genre,
            year,
            popularity,
            track["duration"],
            album_cover_url,
        ))

        if any(word in track["title"] for word in ["Anniversary", "Remaster"]): #probably wrong release year

            # cursor.execute("""
            #                 SELECT id FROM tracks WHERE deezer_id = ?
            #             """, (track["id"],))
            #
            # row = cursor.fetchone()
            # row_id = row[0] if row else None
            #
            # # if row_id:
            # #     print(track["title"], row_id)

            data["songs"].append({
                "name": track["title_short"],
                "artist":  track["artist"]["name"],
                "release_year": year,
                "id": track["id"] #get the row
            })

    #call to agent.py to correct data
    data = correct_release_year(data).model_dump()

    #insert the corrected yeear in databasee
    for song in data["songs"]:
        cursor.execute("""
            UPDATE tracks
            SET year = ?
            WHERE deezer_id = ?
        """, (song["release_year"], song["id"]))

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


def get_tracks(
        nb_tracks: int,
        genre: str = None,
        artist: str = None,
        min_year: int = None,
        max_year: int = None
) -> list:
    """Read into the database to get tracks.

    Parameters
    ----------
    nb_tracks : int
        numbers of tracks wanted.
    genre : str
        filter by genre
    artist : str
        filter by artist
    min_year: int:
        filter by minimum release year for a song.
    max_year: int
        filter by maximum release year for a song.

    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT * FROM tracks WHERE preview_path IS NOT NULL"
    params = []

    # optionnals filters
    conditions = []
    if genre:
        conditions.append("genre = ?")
        params.append(genre)
    if artist:
        conditions.append("artist = ?")
        params.append(artist)
    if min_year:
        conditions.append("year >= ?")
        params.append(min_year)
    if max_year:
        conditions.append("year <= ?")
        params.append(max_year)
    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY RANDOM() LIMIT ?"
    params.append(nb_tracks)

    cursor.execute(query, params)
    rows = cursor.fetchall()



    conn.close()
    return rows


def get_genres() -> list:
    """Read into the database to get genres.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT genre
        FROM tracks
        WHERE genre IS NOT NULL
    """
    query += " ORDER BY genre ASC"

    cursor.execute(query)
    rows = cursor.fetchall()

    conn.close()

    # Optionnel : transformer [(genre,), ...] en [genre, ...]
    genres = [row[0] for row in rows]

    return genres


def download_preview(
        deezer_id: int
) -> str | None:
    """Download a preview of a track

    Parameters
    ----------
    deezer_id : int
        deezer id of the track.
    """
    #fetch the preview url which is temporary
    response_id = requests.get(f"https://api.deezer.com/track/{deezer_id}")
    track = response_id.json()
    preview_url = track["preview"]
    response_preview = requests.get(preview_url)

    preview_path = BASE_DIR / "data" / "music" / f"{deezer_id}.mp3"
    with open(preview_path, "wb") as f:
        f.write(response_preview.content)

    # Update database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tracks SET preview_path = ? WHERE deezer_id = ?",
                   (str(preview_path), deezer_id))
    conn.commit()
    conn.close()
    return str(preview_path)


def download_all_previews():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT deezer_id FROM tracks WHERE preview_path IS NULL")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        deezer_id = row[0]
        path = download_preview(deezer_id)
        print(f"Downloaded {deezer_id}")

def download_album_cover(
    url: str,
    track_id: int
) -> str | None:

    response = requests.get(url)
    # if response.status_code != 200 or len(response.content) < 1000:
    #     print(f"Skipping {track_id} - failed response")
    #     return None

    cover_path = BASE_DIR / "data" / "covers" / f"{track_id}.jpg"
    with open(cover_path, "wb") as f:
        f.write(response.content)

    # Update database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tracks SET album_cover_path = ? WHERE deezer_id = ?",
                   (str(cover_path), track_id))
    conn.commit()
    conn.close()
    return str(cover_path)

def download_all_album_covers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT deezer_id, album_cover_url FROM tracks WHERE album_cover_path IS NULL")
    rows = cursor.fetchall()
    conn.close()

    for deezer_id, album_cover_url in rows:
        if album_cover_url:
            path = download_album_cover(album_cover_url, deezer_id)
            print(f"Downloaded {deezer_id}")

def clean_db():
    """Clean the database from eventual corrupted files.

    """
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
    print(f"{cleaned} cleaned entries")