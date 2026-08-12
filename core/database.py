import os
import sqlite3
import time
from pathlib import Path
from moviepy import VideoFileClip
from ai.agents import correct_release_year, is_official_clip
from core.audio import BASE_DIR
import requests
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import tempfile
import shutil

from core.genres import GENRE_TREE

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

GENRE_NAMES = {
    132: "Pop",
    116: "Rap/Hip Hop",
    152: "Rock",
    113: "Dance",
    165: "R&B",
    85: "Alternative",
    106: "Electro",
    52: "Chanson française",
    144: "Reggae",
    129: "Jazz",
    464: "Metal",
    169: "Soul & Funk",
    153: "Blues",
    197: "Latino",
}

def _album_genre_names(album_data: dict) -> list[str]:
    return [
        genre["name"]
        for genre in album_data.get("genres", {}).get("data", [])
    ]

def init_db():
    """Create a database to store musics with their datas to generate blindtest
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
            subgenre TEXT,
            year INTEGER,
            popularity INTEGER,
            duration INTEGER,
            country TEXT,
            preview_path TEXT,
            album_cover_url TEXT,
            album_cover_path TEXT,
            video_path TEXT,
            deezer_id INTEGER UNIQUE
        )
    """)
    conn.commit()
    conn.close()


def _insert_tracks(tracks: list):
    """
    Insert tracks into database.

    Parameters
    ----------
    tracks : list
        list of tracks from deezer API.
    """

    data = {
        "songs": []
    }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for track in tracks:

        track_id = track["id"]

        full_track = requests.get(
            f"https://api.deezer.com/track/{track_id}"
        ).json()

        #get isrc track to get the country
        isrc = full_track.get("isrc")
        country = isrc[:2] if isrc else None

        album_id = track["album"]["id"]

        album_data = track.get("_album_data") or requests.get(
            f"https://api.deezer.com/album/{album_id}"
        ).json()

        album_cover_url = album_data.get("cover_big")

        year = (
            int(album_data["release_date"][:4])
            if album_data.get("release_date")
            else None
        )

        popularity = track.get("rank")

        genre = track.get("genre")
        subgenre = track.get("subgenre")

        cursor.execute("""
            INSERT OR IGNORE INTO tracks (
                deezer_id,
                title,
                artist,
                album,
                genre,
                subgenre,
                year,
                popularity,
                duration,
                country,
                album_cover_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            track_id,
            track["title_short"],
            track["artist"]["name"],
            track["album"]["title"],
            genre,
            subgenre,
            year,
            popularity,
            track["duration"],
            country,
            album_cover_url,
        ))

        keywords = [
            "anniversary",
            "remaster",
            "anniversaire",
            "deluxe",
            "remastered",
            "best",
            "edition",
        ]

        if any(word in track["title"].lower() for word in keywords) or any(word in track["album"]["title"].lower() for word in keywords):
            data["songs"].append({
                "name": track["title_short"],
                "artist": track["artist"]["name"],
                "release_year": year,
                "id": track_id,
            })

    if data["songs"]: #call to agent.py to correct release year
        data = correct_release_year(data).model_dump()

        for song in data["songs"]:
            cursor.execute("""
                UPDATE tracks
                SET year = ?
                WHERE deezer_id = ?
            """, (
                song["release_year"],
                song["id"]
            ))

    conn.commit()
    conn.close()

def search_and_import(
    query: str,
    genre: str,
    subgenre: str,
    nb_tracks: int = 1,
):
    """
    Search and fetch 1 (or more) music from a query to the deezer API.

    Parameters
    ----------
    query : str
        Music to import.
    genre : str
        genre of the music to import.
    subgenre : str
        subgenre associated to a global genre (see genres.py)
    nb_tracks: int
        number of tracks to import from the query.
    """
    response = requests.get(
        f"https://api.deezer.com/search?q={query}&limit={nb_tracks}"
    ).json()

    tracks = response.get("data", [])

    for track in tracks:
        if "artist" not in track:
            continue
        track["genre"] = genre
        track["subgenre"] = subgenre
        track["artist_name"] = track["artist"]["name"]

    _insert_tracks(tracks)

_SUSPICIOUS_ARTIST_KEYWORDS = ["cover", "tribute", "orchestra", "karaoke", "instrumental"]

def import_movies_series(
        genre_name: str,
        nb_tracks: int
) -> list:
    """
    Import movie/series themes from Deezer using the query -> display title
    mapping from genres.py.

    Unlike import_by_genre (which searches by artist and takes their top
    tracks), this searches directly for the theme/track title, since a movie
    composer's Deezer "top tracks" rarely map to one specific film. The
    artist field is overwritten with the movie/show title before insertion,
    so the blindtest reveal shows the title rather than the composer name.

    Parameters
    ----------
    genre_name : str
        "movies" or "series".
    nb_tracks : int
        max number of tracks to import for this genre.

    Returns
    -------
    list
        List of tracks fetched from deezer API.
    """
    genre_name = genre_name.lower()

    subgenres = GENRE_TREE.get(genre_name)
    if subgenres is None:
        raise ValueError(f"Unknown genre: {genre_name}")

    collected = []

    for subgenre_name, entries in subgenres.items():

        for query, display_title in entries.items():

            if len(collected) >= nb_tracks:
                break

            response = requests.get(
                f"https://api.deezer.com/search?q={query}&limit=3"
            ).json()

            candidates = response.get("data", [])

            track = None
            for candidate in candidates:
                if "artist" not in candidate:
                    continue
                artist_name = candidate["artist"]["name"].lower()
                if any(keyword in artist_name for keyword in _SUSPICIOUS_ARTIST_KEYWORDS):
                    continue
                track = candidate
                break

            if track is None:
                print(f"[import_movies_series] no clean result for {query!r} ({display_title}), skipped")
                continue

            track["genre"] = genre_name
            track["subgenre"] = subgenre_name
            track["artist"]["name"] = display_title
            track["artist_name"] = display_title

            collected.append(track)

        if len(collected) >= nb_tracks:
            break

    _insert_tracks(collected)
    return collected

def _deezer_search_artist_id(
        artist_name: str
)-> int | None:
    """Retrieve deezer id of an artist

    Parameters
    ----------
    artist_name : str
        Name of the artist.

    Returns
    -------
    int | None
        id of the artist or None if not found.
    """
    url = f"https://api.deezer.com/search/artist?q={artist_name}"
    data = requests.get(url).json()

    if "data" not in data or len(data["data"]) == 0:
        return None

    return data["data"][0]["id"]


def import_by_genre(
        genre_name: str,
        nb_tracks: int
) ->list:
    """
    Import music by genre from deezer API. This function will use genre_tree
    from genres.py to import a genre and all subgenre from a list of artist to ensure
    geenre validity.

    Parameters
    ----------
    genre_name : str,
        genre to import: "rock","pop","rap","chanson_fr","electro","metal"
    nb_tracks : int
        number of tracks to import

    Returns
    -------
    list
        List of tracks fetched from deezer API.

    """
    genre_name = genre_name.lower()

    subgenres = GENRE_TREE.get(genre_name)
    if subgenres is None:
        raise ValueError(f"Unknown genre: {genre_name}")

    collected = []
    seen_track_ids = set()

    for subgenre_name, artists in subgenres.items():

        for artist_name in artists:

            if len(collected) >= nb_tracks:
                break

            artist_id = _deezer_search_artist_id(artist_name)
            if not artist_id:
                continue

            tracks = requests.get(
                f"https://api.deezer.com/artist/{artist_id}/top?limit=10"
            ).json().get("data", [])

            count = 0

            for track in tracks:
                if len(collected) >= nb_tracks:
                    break

                if track["id"] in seen_track_ids:
                    continue

                track["genre"] = genre_name
                track["subgenre"] = subgenre_name
                track["artist_name"] = artist_name
                track["artist_id"] = artist_id

                seen_track_ids.add(track["id"])
                collected.append(track)

                count += 1

                # 3 tracks per artist, could be more
                if count >= 3:
                    break

        if len(collected) >= nb_tracks:
            break

    _insert_tracks(collected)
    return collected

#deprecated
# def import_charts(nb_tracks: int):
#     response = requests.get(f"https://api.deezer.com/chart/0/tracks?limit={nb_tracks}")
#     _insert_tracks(response.json()["data"])

def import_by_artist(
    artist_name: str,
    nb_tracks: int,
    genre: str,
    subgenre: str
):
    """
    Fetch nb_tracks music from a given artist name from deezer API.

    Warning
    -------
    Deezer's catalog depth varies a lot per artist: mainstream artists
    (e.g. Gorillaz) can return the full nb_tracks requested, but less
    popular/niche artists may only have a handful of tracks referenced
    on Deezer. This function does not raise if fewer tracks than
    nb_tracks are found, it just inserts whatever was returned. If you
    need a guaranteed count (e.g. for a single-artist blindtest), check
    the actual number of tracks in the db for that artist afterward
    (get_tracks(..., artist=...)) before generating the blindtest.

    Parameters
    ----------
    artist_name : str
        Name of the artist.
    nb_tracks: int
        number of tracks to import from the query.
    genre : str
        genre of the music to import.
    subgenre : str
        subgenre associated to a global genre (see genres.py)
    """
    search = requests.get(
        f"https://api.deezer.com/search/artist?q={artist_name}&limit=1"
    ).json()

    if not search.get("data"):
        return

    artist = search["data"][0]
    artist_id = artist["id"]

    response = requests.get(
        f"https://api.deezer.com/artist/{artist_id}/top?limit={nb_tracks}"
    ).json()

    tracks = response.get("data", [])

    for track in tracks:
        track["genre"] = genre
        track["subgenre"] = subgenre
        track["artist_name"] = artist_name

    _insert_tracks(tracks)


def get_tracks(
        nb_tracks: int,
        genre: str | list[str] = None,
        subgenre: str | list[str] = None,
        artist: str = None,
        min_year: int = None,
        max_year: int = None,
        min_popularity : int = None,
        max_popularity: int = None,
        include_country: list[str] = None,
        exclude_country: list[str] = None,
        max_per_artist: int | None = 2,
) -> list:
    """Read into the database to get tracks for generate_blindtest() function.

    Parameters
    ----------
    nb_tracks : int
        numbers of tracks wanted.
    genre : str
        filter by genre
    subgenre : str
        filter by subgenre
    artist : str
        filter by artist
    min_year: int:
        filter by minimum release year for a song.
    max_year: int
        filter by maximum release year for a song.
    min_popularity : int = None
        filter by popularity int from deezer APi, min=0
    max_popularity : int = None
        filter by popularity int from deezer APi, max=999999
    include_country: list[str] = None
        include country
    exclude_country: list[str] = None
        exclude country
    max_per_artist : int | None = 2
        maximum number of times the same artist can appear in the result.
        Pass None to disable the cap (old behaviour).

    Raises
    ------
    ValueError
        If max_per_artist is not a positive integer, or if the cap makes it
        impossible to reach nb_tracks (fewer tracks available than requested).
    """
    if max_per_artist is not None and max_per_artist <= 0:
        raise ValueError(
            "max_per_artist must be a positive integer, or None to disable the cap "
            "(0 would literally exclude every track)."
        )
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT * FROM tracks WHERE preview_path IS NOT NULL"
    params = []

    # optionnals filters
    conditions = []
    if genre:
        if isinstance(genre, list):
            placeholders = ",".join(["?"] * len(genre))
            conditions.append(f"genre IN ({placeholders})")
            params.extend(genre)
        else:
            conditions.append("genre = ?")
            params.append(genre)
    if subgenre:
        if isinstance(subgenre, list):
            placeholders = ",".join(["?"] * len(subgenre))
            conditions.append(f"subgenre IN ({placeholders})")
            params.extend(subgenre)
        else:
            conditions.append("subgenre = ?")
            params.append(subgenre)
    if artist:
        conditions.append("artist = ?")
        params.append(artist)
    if min_year:
        conditions.append("year >= ?")
        params.append(min_year)
    if max_year:
        conditions.append("year <= ?")
        params.append(max_year)
    if min_popularity:
        conditions.append("popularity >= ? ")
        params.append(min_popularity)
    if max_popularity:
        conditions.append("popularity <= ? ")
        params.append(max_popularity)
    if include_country:
        placeholders = ",".join(["?"] * len(include_country))
        conditions.append(f"country IN ({placeholders})")
        params.extend(include_country)

    if exclude_country:
        placeholders = ",".join(["?"] * len(exclude_country))
        conditions.append(f"country NOT IN ({placeholders})")
        params.extend(exclude_country)
    if conditions:
        query += " AND " + " AND ".join(conditions)

    if max_per_artist is not None:
        query = f"""
            WITH ranked AS (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY artist ORDER BY RANDOM()) AS rn
                FROM ({query})
            )
            SELECT id, title, artist, album, genre, subgenre, year, popularity,
                   duration, country, preview_path, album_cover_url,
                   album_cover_path, video_path, deezer_id
            FROM ranked WHERE rn <= ? ORDER BY RANDOM()
        """
        params.append(max_per_artist)
    else:
        query += " ORDER BY RANDOM()"
    query += " LIMIT ?"
    params.append(nb_tracks)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    conn.close()

    if max_per_artist is not None and len(rows) < nb_tracks:
        raise ValueError(
            f"Only {len(rows)} track(s) available with max_per_artist={max_per_artist} "
            f"(wanted {nb_tracks}). Increase max_per_artist or set it to None to disable the cap."
        )

    return rows


def download_preview(
        deezer_id: int
) -> str | None:
    """Download a preview of a track from deezer API.

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
    """download every preview from deezer for every song in the db using download_preview().
    """
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
    """Download the album cover (.jpg) from deezer.

        Parameters
        ----------
         url: str
            link to the album cover image.
        track_id : int
            deezer id of the song

        Returns
        -------
        str | None
            Return the path to the album cover image.
    """
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
    """download every album cover from deezer for every song in the db using download_album_cover() and write in db.
    """
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


#MUSIC SEARCH
def has_music_video_section(
        artist : str,
        title : str
) -> bool:
    """will search wikipedia, if the song has its own page, it will look for "music video" section
    which is always there if the video exists. If not, return False.
    If the song doesn't have its page its likely that there is not a video for the song.
    The search  will return probably a page of the artist,
    or a list of song or a related page to the artist but it will then not have
    music video in it, so it will return False.

    Parameters
    ----------
    artist : str
        name of the artist.
    title : str
        name of the song.

    Returns
    -------
    bool
        A boolean indicating whether the song has a video section on its wikipedia page.
    """
    base_url = f"https://en.wikipedia.org/w/api.php"

    headers = {
        "User-Agent": "Mozilla/5.0 (music-video-checker/1.0)"
    }

    # 1) Search page
    search_query = f"{artist} {title}"

    try:
        r = requests.get(
            base_url,
            params={
                "action": "query",
                "list": "search",
                "srsearch": search_query,
                "format": "json"
            },
            headers=headers,
            timeout=10
        )

        if r.status_code != 200:
            return False

        data = r.json()

    except Exception:
        return False

    search_results = data.get("query", {}).get("search", [])
    if not search_results:
        return False

    page_title = search_results[0]["title"]

    #Get sections
    try:
        r = requests.get(
            base_url,
            params={
                "action": "parse",
                "page": page_title,
                "prop": "sections",
                "format": "json"
            },
            headers=headers,
            timeout=10
        )

        if r.status_code != 200:
            return False

        data = r.json()

    except Exception:
        return False

    sections = data.get("parse", {}).get("sections", [])
    if not sections:
        return False

    #search in sections
    for s in sections:
        name = s.get("line", "").lower()
        if "music video" in name:
            return True
    return False

def imdb_clip_exists(
        artist_to_search: str,
        title_to_search: str
) -> bool:
    """will search imdb with {artist} - {tile} and check if the first results has the
    mention "music video". More consistent than searching wikipedia for french music,
    but might be better also to look imdb for english or every other music.

    Parameters
    ----------
    artist_to_search : str
        name of the artist.
    title_to_search : str
        name of the song.

    Returns
    -------
    bool
        A boolean indicating whether the song has a video section on its imdb page.
    """
    query = f"{artist_to_search} {title_to_search}"

    url = (
        "https://v2.sg.media-imdb.com/suggestion/t/"
        + query.replace(" ", "%20")
        + ".json"
    )

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return False

    data = response.json()

    results = data.get("d", [])
    for r in results:

        title_text = (r.get("l") or "").lower()
        kind = (r.get("q") or "").lower()

        #should remove " " when looking into strings
        if ("musicvideo" in kind and artist_to_search.lower() in title_text) or ("clip" in kind and artist_to_search.lower() in title_text):# and title_to_search.lower() in title_text :
            return True

    return False

def get_youtube_video_url(
        artist_ytb: str,
        title_ytb: str,
        country: str
) -> str | None:


    # if country == "FR" or country == "BE":
    #     is_video = imdb_clip_exists(artist_ytb, title_ytb) #search imdb
    # else:  # english
    #     is_video = has_music_video_section(artist_ytb, title_ytb) #search wiki
    is_video = imdb_clip_exists(artist_ytb, title_ytb)

    if is_video: #there is an official clip, we take the first youtube return
        query = f"{artist_ytb} - {title_ytb} official video"

        with YoutubeDL({
            "skip_download": True,
            "extract_flat": True,  # evite resolution des videos
        }) as ydl:

            results = ydl.extract_info(f"ytsearch5:{query}", download=False)
            entries = results.get("entries", [])

            if not entries:
                return None

            video = entries[0]

            return f"https://www.youtube.com/watch?v={video['id']}"

    else: #no official video
        return None


def _update_video_path(track_id: int, video_path: str | Path):
    """update video path if the video already exist but the path was lost
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tracks SET video_path = ? WHERE deezer_id = ?",
                   (str(video_path), track_id))
    conn.commit()
    conn.close()


def download_youtube_video(
        track_id: int,
        youtube_url: str,
        video_path: str,
        start_time: int,
        end_time: int,

):
    """Download a YouTube video and crop it between start_time and end_time (No need
    for a full length video when the video only appears for a few seconds in a blindtest).

    Parameters
    ----------
    track_id : int
        deezer id of the track.
    youtube_url: str
        url of the YouTube video to download
    video_path: str
        path to save the video.
    start_time: int
        start time of the video.
    end_time: int
        end of the video to crop.

    Returns
    -------
    """
    #if video is already downloaded, exit
    if os.path.exists(video_path):
        _update_video_path(track_id, video_path)
        return

    temp_dir = tempfile.mkdtemp()

    try:
        ydl_opts = { #options for yt-dlp
                #"format": "bestvideo+bestaudio/best", #best quality but codec not generally compatible
                #"format": "bestvideo[vcodec*=avc1]+bestaudio/best", #avc1 more supported codec
                "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
                "merge_output_format": "mp4",
                "outtmpl": f"{temp_dir}/%(title)s.%(ext)s", #yt-dlp template

                #download parameters
                "socket_timeout": 60,
                "retries": 10,
                "fragment_retries": 10,
                "concurrent_fragment_downloads": 3,

                #"cookiesfrombrowser": ("chrome",), #doesn't seem to work

                # "js_runtimes": {
                #     "node": {
                #         "path": "C:/Program Files/nodejs/node.exe"
                #     }
                # }

            }

        with YoutubeDL(ydl_opts) as ydl:
            #get the info from the url and download it in tempfile
            try:
                info = ydl.extract_info(youtube_url, download=True)
            except DownloadError as e:
                print(f"Skipping YouTube download for {track_id}: {e}")
                return
            temp_file = ydl.prepare_filename(info)
            temp_file = os.path.splitext(temp_file)[0] + ".mp4"

        #moviepy to open,edit and write the final video
        clip = VideoFileClip(temp_file)
        clip = clip.subclipped(start_time, end_time)
        clip.write_videofile(video_path,fps=24)

    finally: #delete tempfile
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Update database
    _update_video_path(track_id, video_path)


def download_all_youtube_videos():
    """download every official youtube video for every song in the db using download_youtube_video() and write in db.

    Skips "movies" and "series" tracks: their `artist` field holds the movie/show
    title rather than a real performer, so there is no "official music video" to
    look for.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, artist, country, deezer_id, video_path, genre FROM tracks")
    rows = cursor.fetchall()
    conn.close()

    start_time, end_time = 60, 75 #default
    count = 0
    for row in rows:
        title = row[0]
        artist = row[1]
        country = row[2]
        track_id = row[3]
        current_video_path = row[4]
        genre = row[5]
        count += 1

        if genre in ("movies", "series"):
            continue

        if current_video_path and Path(current_video_path).exists():
            continue

        video_path = BASE_DIR / "data" / "videos" / f"{track_id}.mp4"
        if video_path.exists():
            _update_video_path(track_id, video_path)
            continue

        try:
            url = get_youtube_video_url(artist, title, country)

            if url is not None:
                download_youtube_video(track_id,url, video_path,start_time, end_time)

                time.sleep(1) #in case of rate limit
        except Exception as e:
            print(f"Skipping video for {artist} - {title}: {e}")


#extracting year correction from _insert_tracks() to replay it on any db
KEYWORDS = [
    "anniversary",
    "remaster",
    "anniversaire",
    "deluxe",
    "remastered",
    "best",
    "edition",
    "michael", #michael jacskon
    "celebration",
    "claude françois",#claude françois
    "mötley",
    "motörhead",
    "chanson"
]

def needs_year_correction(track_title: str, album_title: str, artist_name : str, subgenre_name : str) -> bool:
    title = track_title.lower()
    album = album_title.lower()
    artist = artist_name.lower()
    subgenre = subgenre_name.lower()

    return any(k in title for k in KEYWORDS) or any(k in album for k in KEYWORDS) or any(k in artist for k in KEYWORDS) or any(k in subgenre for k in KEYWORDS)

# def correct_years_in_database():
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
#
#     cursor.execute("""
#         SELECT deezer_id, title, artist, album, year
#         FROM tracks
#     """)
#
#     rows = cursor.fetchall()
#
#     data = {"songs": []}
#
#     for deezer_id, title, artist, album, year in rows:
#
#         if needs_year_correction(title, album, artist):
#             data["songs"].append({
#                 "id": deezer_id,
#                 "name": title,
#                 "artist": artist,
#                 "release_year": year
#             })
#
#     if not data["songs"]:
#         print("No tracks to correct.")
#         return
#
#     corrected = correct_release_year(data).model_dump()
#
#
#     for song in corrected["songs"]:
#         cursor.execute("""
#             UPDATE tracks
#             SET year = ?
#             WHERE deezer_id = ?
#         """, (
#             song["release_year"],
#             song["id"]
#         ))
#
#     conn.commit()
#     conn.close()
#
#     print(corrected)
#     print(f"Corrected {len(corrected['songs'])} tracks")

def correct_years_in_database():
    """Corrige les années de sortie pour toute la base, par lots de 10.

    Ne traite que les pistes détectées par needs_year_correction()
    (mots-clés dans titre/album/artiste/subgenre). Fonctionne bien,
    déjà testée avec succès sur toute la base en une seule exécution.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT deezer_id, title, artist, album, year, subgenre
        FROM tracks
    """)

    rows = cursor.fetchall()

    data = {"songs": []}

    for deezer_id, title, artist, album, year, subgenre in rows:

        if needs_year_correction(title, album, artist, subgenre):
            data["songs"].append({
                "id": deezer_id,
                "name": title,
                "artist": artist,
                "release_year": year
            })

    if not data["songs"]:
        print("No tracks to correct.")
        conn.close()
        return

    corrected_songs = []

    # Traitement par lots de 10
    for i in range(0, len(data["songs"]), 10):
        batch = {"songs": data["songs"][i:i + 10]}

        print(
            f"Processing batch {i//10 + 1} "
            f"({len(batch['songs'])} songs)"
        )

        corrected = correct_release_year(batch).model_dump()

        corrected_songs.extend(corrected["songs"])

    # Mise à jour de la base
    for song in corrected_songs:
        cursor.execute("""
            UPDATE tracks
            SET year = ?
            WHERE deezer_id = ?
        """, (
            song["release_year"],
            song["id"]
        ))

    conn.commit()
    conn.close()

    print(f"Corrected {len(corrected_songs)} tracks")


def correct_all_years_in_database():
    """Corrige les années pour toutes les pistes avec year >= 2000, par lots de 20.

    Ne filtre pas par mots-clés (contrairement à correct_years_in_database),
    donc beaucoup plus d'appels LLM. Marche moins bien en pratique.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT deezer_id, title, artist, year
        FROM tracks
        WHERE year >= 2000
    """)

    rows = cursor.fetchall()

    songs = [
        {
            "id": deezer_id,
            "name": title,
            "artist": artist,
            "release_year": year
        }
        for deezer_id, title, artist, year in rows
    ]

    if not songs:
        print("No tracks to correct.")
        conn.close()
        return

    corrected_songs = []

    total_batches = (len(songs) - 1) // 20 + 1

    for i in range(0, len(songs), 20):
        batch = {"songs": songs[i:i + 20]}

        print(
            f"Processing batch {i // 20 + 1}/{total_batches} "
            f"({len(batch['songs'])} songs)"
        )

        try:
            corrected = correct_release_year(batch).model_dump()
            corrected_songs.extend(corrected["songs"])
        except Exception as e:
            print(
                f"Error while processing batch "
                f"{i // 20 + 1}: {e}"
            )

    for song in corrected_songs:
        cursor.execute("""
            UPDATE tracks
            SET year = ?
            WHERE deezer_id = ?
        """, (
            song["release_year"],
            song["id"]
        ))

    conn.commit()
    conn.close()

    print(f"Corrected {len(corrected_songs)} tracks")
