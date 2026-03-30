from core.database import clean_db
from core.database import get_tracks
from core.audio import AudioTrack, AudioSegment, BASE_DIR
from core.video import build_clip  , assemble_video

def generate_blindtest(
    music_folder: str,
    output_path: str,
    nb_tracks: int = 10,
    guessing_duration: int = 10,
    reveal_duration: int = 5,
    genre: str | list[str] = None ,
    min_year: int = None,
    max_year: int = None,
        ) -> str:
    """Scan data/music folder with deezer previews and generate a blindtest
    video from

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
    clean_db()

    mp3_files = get_tracks(nb_tracks,genre,min_year=min_year,max_year=max_year)
    clips = []
    track_number_counter = 1
    for i in range(len(mp3_files)):
        track = AudioTrack.from_db(mp3_files[i])
        clip, tmp = build_clip(track, track_number_counter, nb_tracks, guessing_duration, reveal_duration)
        clips.append(clip)
        track_number_counter += 1


    assemble_video(clips, output_path)
    return output_path

