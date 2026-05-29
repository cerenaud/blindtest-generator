import base64
from io import BytesIO
from typing import Any

from core.database import get_tracks
from core.video import *
from pydub import AudioSegment
import json

def generate_blindtest_audio(
    music_folder: str,
    output_path: str,
    nb_tracks: int = 10,
    guessing_duration: int = 10,
    reveal_duration: int = 5,
    genre: str | list[str] = None ,
    min_year: int = None,
    max_year: int = None,
) -> tuple[Any, str]:
    """generate an audio blindtest and a json with information about the tracks.

    Parameters
    ----------
    music_folder : path
        path where music files are located.
    output_path : str
        Path where the blindtest video will be saved.
    nb_tracks : int
        number of tracks of the blindtest.
    guessing_duration : int
        duration of the guessing part for a song in the blindtest.
    reveal_duration: int
        duration of the reveal part for a song in the blindtest.
    genre: str | list[str]
        music genre of the blindtest. Could be one or more.
    min_year: int:
        minimum release year for a music to appear in the blindtest.
    max_year: int:
        maximum release year for a music to appear in the blindtest.

    Returns
    -------
    output_path : str
        :the path were the blindtest will be saved.
    """
    blindtest_info = []
    mp3_files = get_tracks(nb_tracks,genre,min_year=min_year,max_year=max_year)
    track_number_counter = 1
    blindtest = AudioSegment.silent(duration=0)
    for i in range(len(mp3_files)):
        track = AudioTrack.from_db(mp3_files[i])
        track_audio = AudioSegment.from_file(track.path)
        track_audio = track_audio[:(guessing_duration+reveal_duration) * 1000]
        track_audio = (
            track_audio
            .fade_in(1500)  # 2 secondes
            .fade_out(1500)  # 3 secondes
        )

        blindtest += track_audio

        with open(track.album_cover_path, "rb") as image_file:
            base64_cover = base64.b64encode(image_file.read())

        blindtest_info.append({
            "title": track.title,
            "artist": track.artist,
            "album": track.album,
            "genre": track.genre,
            "year": track.year,
            "country": track.country,
            "album_cover": base64_cover
        })

        track_number_counter += 1

    blindtest.export(output_path, format="mp3")

    #blindtest_info = json.dumps(blindtest_info)

    return blindtest, blindtest_info

#ex
# blindtest,blindtest_info = generate_blindtest_audio("data/music", "output/blindtest_audio.mp3", 3, 10, 5)
# img_data = base64.b64decode(blindtest_info[0]["album_cover"])
# img = Image.open(BytesIO(img_data))
# img.show()