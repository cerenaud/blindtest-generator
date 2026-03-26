from moviepy import VideoClip, AudioFileClip, concatenate_videoclips
import numpy as np
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
    the song title and the artist. A blindtest is a sequence of different clips

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

