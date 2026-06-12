from core.database import clean_db
from core.database import get_tracks
from core.audio import AudioTrack, AudioSegment, BASE_DIR
from core.video import *
import gc
from pathlib import Path

def generate_blindtest(
    output_path: str,
    intro_text: str,
    intro_background: str,
    intro_song: str,
    outro_background: str,
    outro_song: str,
    nb_tracks: int = 10,
    guessing_duration: int = 10,
    reveal_duration: int = 5,
    genre: str | list[str] = None ,
    min_year: int = None,
    max_year: int = None,
        ) -> str:
    """Generate a blindtest video with parameters and music from db.

    Parameters
    ----------
    output_path : str
        Path where the blindtest video will be saved.
    intro_text : str
        intro text to describe the blindtest.
    intro_background: str
        path to the background video for the intro.
    intro_song: str
        path to the song for the intro.
    outro_background: str
        path to the background video for the outro.
    outro_song: str
        path to the song for the outro.
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
    guessing_background = "data/backgrounds/turntable_25fps.mp4"
    reveal_background = "data/backgrounds/vhs_particle_25fps.mp4"
    for i in range(len(mp3_files)):
        track = AudioTrack.from_db(mp3_files[i])
        # will need to choose, use build_clip_with_video only if the clip exist, else use build_clip to use album cover
        if track.video_path is not None:
            video_path = track.video_path
            clip, tmp = build_clip_with_video_and_background(track, track_number_counter, nb_tracks, video_path,guessing_background, guessing_duration,
                                              reveal_duration)
        else:
            clip, tmp = build_clip_with_background(track, track_number_counter, nb_tracks, guessing_background, reveal_background, guessing_duration, reveal_duration)

        clips.append(clip)
        track_number_counter += 1

    intro = build_intro(10,intro_background,intro_text,intro_song)
    outro = build_outro(8, outro_background,outro_song)
    assemble_video(intro,outro,clips, output_path)
    return output_path


def generate_blindtest_iterative(
    output_path: str,
    intro_text: str,
    intro_background: str,
    intro_song: str,
    outro_background: str,
    outro_song: str,
    guessing_background: str,
    reveal_background: str,
    nb_tracks: int = 10,
    guessing_duration: int = 10,
    reveal_duration: int = 5,
    genre: str | list[str] = None,
    subgenre: str | list[str] = None,
    min_year: int = None,
    max_year: int = None,
    min_popularity : int = None,
    max_popularity: int = None,
) -> str:
    """Generate a blindtest video by generating every clip for every track and
    assemble at the end. This allows to create a blindtest with 30 or more tracks
    without exploding RAM with moviepy.

        Parameters
    ----------
    output_path : str
        Path where the blindtest video will be saved.
    intro_text : str
        intro text to describe the blindtest.
    intro_background: str
        path to the background video for the intro.
    intro_song: str
        path to the song for the intro.
    outro_background: str
        path to the background video for the outro.
    outro_song: str
        path to the song for the outro.
    guessing_background: str
        path to the guessing background video to use.
    reveal_background: str,
        path to the reveal background video to use.
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

    mp3_files = get_tracks(nb_tracks, genre,subgenre, min_year=min_year, max_year=max_year,min_popularity=min_popularity,max_popularity=max_popularity)

    tmp_dir = BASE_DIR / "data" / "tmp_blindtest"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    temp_files = []
    clips = []
    final = None
    track_number_counter = 1

    try:
        intro = build_intro(10, intro_background, intro_text, intro_song)
        intro_path = tmp_dir / "tmp_intro.mp4"
        intro.write_videofile(str(intro_path), fps=35)
        intro.close()
        temp_files.append(intro_path)

        gc.collect()

        for mp3 in mp3_files:
            track = AudioTrack.from_db(mp3)

            if track.video_path:
                clip, tmp = build_clip_with_video_and_background(
                    track,
                    track_number_counter,
                    nb_tracks,
                    track.video_path,
                    guessing_background,
                    guessing_duration,
                    reveal_duration
                )
            else:
                clip, tmp = build_clip_with_background(
                    track,
                    track_number_counter,
                    nb_tracks,
                    guessing_background,
                    reveal_background,
                    guessing_duration,
                    reveal_duration
                )

            tmp_path = tmp_dir / f"tmp_track_{track_number_counter}.mp4"
            clip.write_videofile(str(tmp_path), fps=35)

            clip.close()
            del clip
            del track
            gc.collect()

            try:
                tmp.close()
            except Exception:
                pass

            temp_files.append(tmp_path)
            track_number_counter += 1

        outro = build_outro(8, outro_background, outro_song)
        outro_path = tmp_dir / "tmp_outro.mp4"
        outro.write_videofile(str(outro_path), fps=35)
        outro.close()
        temp_files.append(outro_path)

        gc.collect()

        clips = [VideoFileClip(str(p)) for p in temp_files]
        final = concatenate_videoclips(clips, method="chain")
        final.write_videofile(str(BASE_DIR / output_path), fps=35)

        return output_path

    finally: #deleting every temp file even if the try fails
        if final is not None:
            final.close()

        for clip in clips:
            clip.close()

        gc.collect()

        for path in temp_files:
            try:
                Path(path).unlink(missing_ok=True)
            except PermissionError:
                pass

        try:
            tmp_dir.rmdir()
        except OSError:
            pass

def generate_blindtest_iterative_us(
    output_path: str,
    intro_text: str,
    intro_background: str,
    intro_song: str,
    outro_background: str,
    outro_song: str,
    guessing_background: str,
    reveal_background: str,
    nb_tracks: int = 10,
    guessing_duration: int = 10,
    reveal_duration: int = 5,
    genre: str | list[str] = None,
    subgenre: str | list[str] = None,
    min_year: int = None,
    max_year: int = None,
    min_popularity : int = None,
    max_popularity: int = None,
    include_country: list[str] = None,
    exclude_country: list[str] = None,
) -> str:
    """Generate a blindtest video by generating every clip for every track and
    assemble at the end. This allows to create a blindtest with 30 or more tracks
    without exploding RAM with moviepy.

        Parameters
    ----------
    output_path : str
        Path where the blindtest video will be saved.
    intro_text : str
        intro text to describe the blindtest.
    intro_background: str
        path to the background video for the intro.
    intro_song: str
        path to the song for the intro.
    outro_background: str
        path to the background video for the outro.
    outro_song: str
        path to the song for the outro.
    guessing_background: str
        path to the guessing background video to use.
    reveal_background: str,
        path to the reveal background video to use.
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
    include_country: list[str] = None
        include country
    exclude_country: list[str] = None
        exclude country

    Returns
    -------
    output_path : str
        :the path were the blindtest will be saved.
    """
    clean_db()

    mp3_files = get_tracks(nb_tracks, genre,subgenre, min_year=min_year, max_year=max_year,min_popularity=min_popularity,max_popularity=max_popularity,exclude_country=exclude_country,include_country=include_country)

    tmp_dir = BASE_DIR / "data" / "tmp_blindtest"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    temp_files = []
    clips = []
    final = None
    track_number_counter = 1

    try:
        intro = build_intro_us(15, intro_background, intro_text, intro_song)
        intro_path = tmp_dir / "tmp_intro.mp4"
        intro.write_videofile(str(intro_path), fps=35)
        intro.close()
        temp_files.append(intro_path)

        gc.collect()

        for mp3 in mp3_files:
            track = AudioTrack.from_db(mp3)

            if track.video_path:
                clip, tmp = build_clip_with_video_and_background_us(
                    track,
                    track_number_counter,
                    nb_tracks,
                    track.video_path,
                    guessing_background,
                    guessing_duration,
                    reveal_duration
                )
            else:
                clip, tmp = build_clip_with_background_us(
                    track,
                    track_number_counter,
                    nb_tracks,
                    guessing_background,
                    reveal_background,
                    guessing_duration,
                    reveal_duration
                )

            tmp_path = tmp_dir / f"tmp_track_{track_number_counter}.mp4"
            clip.write_videofile(str(tmp_path), fps=35)

            clip.close()
            del clip
            del track
            gc.collect()

            try:
                tmp.close()
            except Exception:
                pass

            temp_files.append(tmp_path)
            track_number_counter += 1

        outro = build_outro_us(13, outro_background, outro_song)
        outro_path = tmp_dir / "tmp_outro.mp4"
        outro.write_videofile(str(outro_path), fps=35)
        outro.close()
        temp_files.append(outro_path)

        gc.collect()

        clips = [VideoFileClip(str(p)) for p in temp_files]
        final = concatenate_videoclips(clips, method="chain")
        final.write_videofile(str(BASE_DIR / output_path), fps=35)

        return output_path

    finally: #deleting every temp file even if the try fails
        if final is not None:
            final.close()

        for clip in clips:
            clip.close()

        gc.collect()

        for path in temp_files:
            try:
                Path(path).unlink(missing_ok=True)
            except PermissionError:
                pass

        try:
            tmp_dir.rmdir()
        except OSError:
            pass