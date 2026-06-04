import os
import sqlite3
from pathlib import Path
from moviepy import VideoFileClip
from ai.agents import correct_release_year, is_official_clip
from core.audio import BASE_DIR
import requests
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import tempfile
import shutil

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
    # for track in tracks:
    #     # Appel supplémentaire pour genre et year
    #     album_id = track["album"]["id"]
    #     album_data = requests.get(f"https://api.deezer.com/album/{album_id}").json()
    #     album_cover_url = album_data.get("cover_big", None)
    #     genre = album_data["genres"]["data"][0]["name"] if album_data["genres"]["data"] else None
    #     year = int(album_data["release_date"][:4]) if "release_date" in album_data else None
    #     popularity = track.get("rank", None)
    #
    #     cursor.execute("""
    #         INSERT OR IGNORE INTO tracks (deezer_id, title, artist, album, genre, year, popularity, duration, country, album_cover_url)
    #         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?)
    #     """, (
    #         track["id"],
    #         track["title_short"],
    #         track["artist"]["name"],
    #         track["album"]["title"],
    #         genre,
    #         year,
    #         popularity,
    #         track["duration"],
    #         track["isrc"][:2], #extract the 2 first character to get the country
    #         album_cover_url,
    #     ))
    #
    for track in tracks:

        track_id = track["id"]

        # FULL TRACK DATA (contains isrc)
        full_track = requests.get(
            f"https://api.deezer.com/track/{track_id}"
        ).json()

        isrc = full_track.get("isrc")
        country = isrc[:2] if isrc else None

        # album infos
        album_id = track["album"]["id"]

        album_data = track.get("_album_data") or requests.get(
            f"https://api.deezer.com/album/{album_id}"
        ).json()

        album_cover_url = album_data.get("cover_big")

        album_genres = _album_genre_names(album_data)
        genre = album_genres[0] if album_genres else None

        year = (
            int(album_data["release_date"][:4])
            if album_data.get("release_date")
            else None
        )

        popularity = track.get("rank")

        cursor.execute("""
            INSERT OR IGNORE INTO tracks (
                deezer_id,
                title,
                artist,
                album,
                genre,
                year,
                popularity,
                duration,
                country,
                album_cover_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            track_id,
            track["title_short"],
            track["artist"]["name"],
            track["album"]["title"],
            genre,
            year,
            popularity,
            track["duration"],
            country,
            album_cover_url,
        ))

        if any(word in track["title"] for word in ["Anniversary", "Remaster", "Anniversaire", "Deluxe", "Remastered", "Best", "deluxe", "Edition"]): #probably wrong release year

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

def _deezer_data(url: str) -> list:
    response = requests.get(url)
    response.raise_for_status()
    return response.json().get("data", [])

def import_by_genre(genre_id: int, nb_tracks: int):
    genre_name = GENRE_NAMES.get(genre_id)
    if genre_name is None:
        raise ValueError(f"Unknown Deezer genre id: {genre_id}")

    collected = []
    seen_track_ids = set()
    artist_index = 0

    while len(collected) < nb_tracks:
        artists = _deezer_data(
            f"https://api.deezer.com/genre/{genre_id}/artists"
            f"?limit=100&index={artist_index}"
        )

        if not artists:
            break

        for artist in artists:
            tracks = _deezer_data(
                f"https://api.deezer.com/artist/{artist['id']}/top?limit=100"
            )

            for track in tracks:
                if track["id"] in seen_track_ids:
                    continue

                album_id = track["album"]["id"]
                album_data = requests.get(
                    f"https://api.deezer.com/album/{album_id}"
                ).json()
                album_genres = _album_genre_names(album_data)

                if genre_name not in album_genres:
                    continue

                track["_album_data"] = album_data
                seen_track_ids.add(track["id"])
                collected.append(track)

                if len(collected) >= nb_tracks:
                    break

            if len(collected) >= nb_tracks:
                break

        artist_index += 100
    print(collected)
    _insert_tracks(collected)

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
        if "musicvideo" in kind and artist_to_search.lower() in title_text:# and title_to_search.lower() in title_text :
            return True

    return False

def get_youtube_video_url(
        artist_ytb: str,
        title_ytb: str,
        country: str
) -> str | None:


    if country == "FR" or country == "BE":
        is_video = imdb_clip_exists(artist_ytb, title_ytb) #search imdb
    else:  # english
        is_video = has_music_video_section(artist_ytb, title_ytb) #search wiki

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
    """Download a youtube video and crop it between start_time and end_time (No need
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
                "format": "bestvideo[vcodec*=avc1]+bestaudio/best", #avc1 more supported codec
                "merge_output_format": "mp4",
                "outtmpl": f"{temp_dir}/%(title)s.%(ext)s", #yt-dlp teemplate
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
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, artist, country, deezer_id, video_path FROM tracks")
    rows = cursor.fetchall()
    conn.close()

    start_time, end_time = 60, 75 #default
    for row in rows:
        title = row[0]
        artist = row[1]
        country = row[2]
        track_id = row[3]
        current_video_path = row[4]

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
        except Exception as e:
            print(f"Skipping video for {artist} - {title}: {e}")
