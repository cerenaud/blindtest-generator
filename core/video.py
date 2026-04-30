from moviepy import VideoClip, AudioFileClip, concatenate_videoclips, VideoFileClip, TextClip, CompositeVideoClip
import numpy as np
from numba.core.ir_utils import replace_vars

from core.visuals import make_guessing_frame, make_reveal_frame
from core.audio import AudioTrack, AudioSegment, BASE_DIR
import tempfile

def build_clip(
        track: AudioTrack,
        track_number: int,
        total_tracks: int,
        guessing_duration: int = 10,
        reveal_duration: int = 5,
) -> tuple[VideoClip,str] :
    """Create a clip for a given song (from an AudioTrack object). A clip is composed of
    different frame to guess a song (usually about 10 seconds) and a reveal frame showing
    the song title and the artist and the cover of the song. A blindtest is a sequence of different clips

        Parameters
        ----------
        track : AudioTrack
            The song track from which the clip will be build
        track_number : int
            Index of the current track in the blindtest.
        total_tracks
            Total number of tracks in the blindtest.
        guessing_duration : int
            Duration in s of the guessing frame
        reveal_duration : int
            Duration in s of the reveal frame

        Returns
        -------
        tuple[VideoClip,str]
            A video clip for a song and a temp path
        """
    total_duration = guessing_duration + reveal_duration
    excerpt = track.get_excerpt(0, total_duration * 1000) #from ms to s
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    excerpt.export(tmp.name, format="mp3")
    tmp.close()

    def make_guessing_frame_to_numpy(
            t : int
    ) -> np.ndarray :
        """Convert a frame to a numpy array for moviepy to create a video clip with
        different arrays

        Parameters
        ----------
        t : int
            time of the remaining countdown.

        Returns
        -------
        np.array
            A np.array of the guessing frame
        """
        countdown = guessing_duration - int(t)
        frame = make_guessing_frame(countdown, track_number, total_tracks)
        return np.array(frame)

    def make_reveal_frame_to_numpy(_) -> np.ndarray:
        frame = make_reveal_frame(track.artist, track.title, track.album_cover_path)
        return np.array(frame)

    guessing_clip = VideoClip(make_guessing_frame_to_numpy, duration=guessing_duration)
    audio_clip = AudioFileClip(tmp.name)
    guessing_clip = guessing_clip.with_audio(audio_clip)

    reveal_clip = VideoClip(make_reveal_frame_to_numpy, duration=reveal_duration)

    final_clip = concatenate_videoclips([guessing_clip, reveal_clip])
    final_clip = final_clip.with_audio(audio_clip)

    return final_clip, tmp.name

def build_clip_with_video(
        track: AudioTrack,
        track_number: int,
        total_tracks: int,
        video_path: str,
        guessing_duration: int = 10,
        reveal_duration: int = 5,
) -> tuple[VideoClip,str] :
    """Create a clip for a given song (from an AudioTrack object). A clip is composed of
    different frame to guess a song (usually about 10 seconds) and a reveal frame showing
    the song title and the artist. A blindtest is a sequence of different clips
    This function add an excerpt of the videoclip of the song instead of the album cover.

        Parameters
        ----------
        track : AudioTrack
            The song track from which the clip will be build
        track_number : int
            Index of the current track in the blindtest.
        total_tracks: int
            Total number of tracks in the blindtest.
        video_path: str
            path to official video clip of the song
        guessing_duration : int
            Duration in s of the guessing frame
        reveal_duration : int
            Duration in s of the reveal frame

        Returns
        -------
        tuple[VideoClip,str]
            A video clip for a song and a temp path
        """
    total_duration = guessing_duration + reveal_duration
    excerpt = track.get_excerpt(0, total_duration * 1000) #from ms to s
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    excerpt.export(tmp.name, format="mp3")
    tmp.close()

    def make_guessing_frame_to_numpy(
            t : int
    ) -> np.ndarray :
        """Convert a frame to a numpy array for moviepy to create a video clip with
        different arrays

        Parameters
        ----------
        t : int
            time of the remaining countdown.

        Returns
        -------
        np.array
            A np.array of the guessing frame
        """
        countdown = guessing_duration - int(t)
        frame = make_guessing_frame(countdown, track_number, total_tracks)
        return np.array(frame)

    guessing_clip = VideoClip(make_guessing_frame_to_numpy, duration=guessing_duration)
    audio_clip = AudioFileClip(tmp.name)
    guessing_clip = guessing_clip.with_audio(audio_clip)

    #TODO: dont hardcode target_resolution
    reveal_video = VideoFileClip(video_path,target_resolution=(1920,1080))
    #can changge start_time to synch with the audio of the preview
    reveal_video = reveal_video.subclipped(0, reveal_duration)

    #text to add to reveal video
    shadow = TextClip(
        text=f"{track.artist} - {track.title}",
        font="arial",
        font_size= 75 if len(f"{track.artist} - {track.title}") < 30 else 55,
        color="black",
        method="label",
        text_align="center",
        size=(1600,100)
    ).with_position(("center", 805)).with_duration(reveal_duration)

    txt_clip = TextClip(
        text=f"{track.artist} - {track.title}",
        font="arial",
        font_size= 75 if len(f"{track.artist} - {track.title}") < 30 else 55,
        color="white",
        method="label",
        text_align="center",
        size=(1600,100)
    ).with_position(("center", 800)).with_duration(reveal_duration)


    reveal_video = CompositeVideoClip([reveal_video,shadow, txt_clip])

    #compose because we have a numpy videoclip (guessingg_clip) and a videofileclip (reveal_video)
    #TODO: add a transition clip with the parameter "transition"
    final_clip = concatenate_videoclips([guessing_clip, reveal_video],method="compose")
    final_clip = final_clip.with_audio(audio_clip)

    return final_clip, tmp.name


def assemble_video(
        clips: list,
        output_path: str
) -> None :
    """Assemble a list of different clips to make a video

    Parameters
    ----------
    clips : list
        a list of clips built by buil_clips
    output_path : str
        the path to the output video file

    Returns
    -------
    None
    """
    print(output_path)
    print(type(output_path))
    final = concatenate_videoclips(clips)
    final.write_videofile(str(BASE_DIR / output_path), fps=24)

