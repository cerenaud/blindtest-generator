from moviepy import VideoClip, AudioFileClip, concatenate_videoclips, VideoFileClip, TextClip, CompositeVideoClip, \
    ColorClip, ImageClip
import numpy as np
from core.visuals import make_guessing_frame, make_reveal_frame
from core.audio import AudioTrack, AudioSegment, BASE_DIR
import tempfile
from moviepy.video.fx import FadeIn, FadeOut, Loop
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
from PIL import Image, ImageDraw, ImageFont

def build_clip(
        track: AudioTrack,
        track_number: int,
        total_tracks: int,
        guessing_duration: int = 10,
        reveal_duration: int = 5,
        video_fade_in: int = 1,
        video_fade_out: int = 1,
        audio_fade_in: int = 1,
        audio_fade_out: int=2
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
        video_fade_in: int
            duration (in s) to fade into the video clip
        video_fade_out: int
            duration (in s) to fade out of the video clip
        audio_fade_in: int
            duration (in s) of the fade in of the audio
        audio_fade_out
            duration (in s) of the fade ou of the audio

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

    final_clip = final_clip.with_effects([
        FadeIn(video_fade_in),
        FadeOut(video_fade_out)
    ])

    final_clip = final_clip.with_audio(audio_clip).with_effects([
        AudioFadeIn(audio_fade_in),
        AudioFadeOut(audio_fade_out)
    ])
    #final_clip = final_clip.with_audio(audio_clip)

    return final_clip, tmp.name

def build_clip_with_video(
        track: AudioTrack,
        track_number: int,
        total_tracks: int,
        video_path: str,
        guessing_duration: int = 10,
        reveal_duration: int = 5,
        video_fade_in: int = 1,
        video_fade_out: int = 1,
        audio_fade_in: int = 1,
        audio_fade_out: int=2
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
        video_fade_in: int
            duration (in s) to fade into the video clip
        video_fade_out: int
            duration (in s) to fade out of the video clip
        audio_fade_in: int
            duration (in s) of the fade in of the audio
        audio_fade_out
            duration (in s) of the fade ou of the audio


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
    #can change start_time to synch with the audio of the preview
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
    #final_clip = final_clip.with_audio(audio_clip)
    final_clip = final_clip.with_effects([
        FadeIn(video_fade_in),
        FadeOut(video_fade_out)
    ])

    final_clip = final_clip.with_audio(audio_clip).with_effects([
        AudioFadeIn(audio_fade_in),
        AudioFadeOut(audio_fade_out)
    ])

    return final_clip, tmp.name

def build_clip_with_background(
        track: AudioTrack,
        track_number: int,
        total_tracks: int,
        guessing_background: str,
        reveal_background: str,
        guessing_duration: int = 10,
        reveal_duration: int = 5,
        video_fade_in: int = 1,
        video_fade_out: int = 1,
        audio_fade_in: int = 1,
        audio_fade_out: int=2
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
        guessing_background: str
            path to the background video for the guessing part.
        reveal_background: str
            path to the background video for the reveal part
        guessing_duration : int
            Duration in s of the guessing frame
        reveal_duration : int
            Duration in s of the reveal frame
        video_fade_in: int
            duration (in s) to fade into the video clip
        video_fade_out: int
            duration (in s) to fade out of the video clip
        audio_fade_in: int
            duration (in s) of the fade in of the audio
        audio_fade_out
            duration (in s) of the fade ou of the audio

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

    def make_frame(t):
        """function to display countdown and track number on the background video
        """
        remaining = max(0, guessing_duration - int(t))

        width = 1920
        height = 1080

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype("arial.ttf", 250)

        text = str(remaining)

        # taille réelle du texte
        bbox = draw.textbbox((0, 0), text, font=font)

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # coordonnées centrées
        x = (width - text_width) / 2
        y = (height - text_height) / 2 - height * 0.1

        draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 255, 255, 255),
            #neon effect
            #stroke_width = 8,
            #stroke_fill = (0, 255, 255, 255)
        )

        draw.text(
            (width // 2, height // 20),
            f"Extrait {track_number} / {total_tracks}",
            fill=(255, 255, 255),
            font=ImageFont.truetype("arial.ttf", 40),
            anchor="mm")

        return np.array(img)

    countdown = VideoClip(
        make_frame,
        duration=guessing_duration
    )

    background = ( #background video
        VideoFileClip(guessing_background)
        .with_effects([Loop(duration=guessing_duration)])
        .resized((1920, 1080))
    )


    #pulse effect
    # countdown = countdown.resized(
    #     lambda t: 1 + 0.05 * np.sin(t * 6)
    # )

    #Progress bar
    bar_width = 1400
    bar_height = 20
    bar_x = 260
    bar_y = 1000

    progress = ColorClip(
        size=(bar_width, bar_height),
        color=(255, 255, 255)
    )

    progress = progress.resized(
        lambda t: (
            max(1, int(bar_width * (1 - t / guessing_duration))),
            bar_height
        )
    )

    #right anchor
    progress = progress.with_position(
        lambda t: (
            bar_x + bar_width - max(1, int(bar_width * (1 - t / guessing_duration))),
            bar_y
        )
    )

    background_bar = ColorClip(
        size=(1400, 20),
        color=(10, 10, 10)
    ).with_position((260, 1000))

    #guessing clip with the backgground video, coutwdown and progress bar
    guessing_clip = CompositeVideoClip([
        background,
        countdown,
        background_bar,
        progress,
    ]).with_duration(guessing_duration)

    audio_clip = AudioFileClip(tmp.name)
    guessing_clip = guessing_clip.with_audio(audio_clip)

    #reveal clip
    background_reveal = (
        VideoFileClip(reveal_background)
        .with_effects([Loop(duration=reveal_duration)])
        .resized((1920, 1080))
    )

    album_cover = (
        ImageClip(track.album_cover_path)
        .resized(height=700)
        .with_duration(reveal_duration)
        .with_position("center")
    )
    album_cover = album_cover.with_position(
        ("center", int(1080 * 0.05))
    )

    shadow = TextClip(
        text=f"{track.artist} - {track.title}",
        font="arial",
        font_size=75 if len(f"{track.artist} - {track.title}") < 30 else 55,
        color="black",
        method="label",
        text_align="center",
        size=(1600, 100)
    ).with_position(("center", 805)).with_duration(reveal_duration)

    txt_clip = TextClip(
        text=f"{track.artist} - {track.title}",
        font="arial",
        font_size=75 if len(f"{track.artist} - {track.title}") < 30 else 55,
        color="white",
        method="label",
        text_align="center",
        size=(1600, 100)
    ).with_position(("center", 800)).with_duration(reveal_duration)

    overlay = ColorClip(
        size=(1920, 1080),
        color=(0, 0, 0)
    ).with_opacity(0.35).with_duration(reveal_duration)

    reveal_clip = CompositeVideoClip([
        background_reveal,
        overlay,
        album_cover,
        shadow,
        txt_clip
    ])

    #Final clip
    final_clip = concatenate_videoclips([guessing_clip, reveal_clip])

    final_clip = final_clip.with_effects([
        FadeIn(video_fade_in),
        FadeOut(video_fade_out)
    ])

    final_clip = final_clip.with_audio(audio_clip).with_effects([
        AudioFadeIn(audio_fade_in),
        AudioFadeOut(audio_fade_out)
    ])

    return final_clip, tmp.name

def build_clip_with_video_and_background(
        track: AudioTrack,
        track_number: int,
        total_tracks: int,
        video_path: str,
        guessing_background: str,
        guessing_duration: int = 10,
        reveal_duration: int = 5,
        video_fade_in: int = 1,
        video_fade_out: int = 1,
        audio_fade_in: int = 1,
        audio_fade_out: int=2
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
        guessing_background: str
            path to the background video for the guessing part
        guessing_duration : int
            Duration in s of the guessing frame
        reveal_duration : int
            Duration in s of the reveal frame
        video_fade_in: int
            duration (in s) to fade into the video clip
        video_fade_out: int
            duration (in s) to fade out of the video clip
        audio_fade_in: int
            duration (in s) of the fade in of the audio
        audio_fade_out
            duration (in s) of the fade ou of the audio


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

    background = (
        VideoFileClip(guessing_background)
        .with_effects([Loop(duration=guessing_duration)])
        .resized((1920, 1080))
    )

    def make_frame(t):
        """function to display countdown and track number on the background video
        """
        remaining = max(0, guessing_duration - int(t))

        width = 1920
        height = 1080

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype("arial.ttf", 250)

        text = str(remaining)

        bbox = draw.textbbox((0, 0), text, font=font)

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) / 2
        y = (height - text_height) / 2 - height * 0.1

        draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 255, 255, 255),
            #neon effect
            #stroke_width = 8,
            #stroke_fill = (0, 255, 255, 255)
        )

        draw.text(
            (width // 2, height // 20),
            f"Extrait {track_number} / {total_tracks}",
            fill=(255, 255, 255),
            font=ImageFont.truetype("arial.ttf", 40),
            anchor="mm")

        return np.array(img)

    countdown = VideoClip(
        make_frame,
        duration=guessing_duration
    )

    #pulse effect
    # countdown = countdown.resized(
    #     lambda t: 1 + 0.05 * np.sin(t * 6)
    # )

    #progress bar
    bar_width = 1400
    bar_height = 20
    bar_x = 260
    bar_y = 1000

    progress = ColorClip(
        size=(bar_width, bar_height),
        color=(255, 255, 255)
    )

    progress = progress.resized(
        lambda t: (
            max(1, int(bar_width * (1 - t / guessing_duration))),
            bar_height
        )
    )

    progress = progress.with_position(
        lambda t: (
            bar_x + bar_width - max(1, int(bar_width * (1 - t / guessing_duration))),
            bar_y
        )
    )

    background_bar = ColorClip(
        size=(1400, 20),
        color=(10, 10, 10)
    ).with_position((260, 1000))

    #guessing clip
    guessing_clip = CompositeVideoClip([
        background,
        countdown,
        background_bar,
        progress,
    ]).with_duration(guessing_duration)

    audio_clip = AudioFileClip(tmp.name)
    guessing_clip = guessing_clip.with_audio(audio_clip)

    #TODO: dont hardcode target_resolution?
    reveal_video = VideoFileClip(video_path,target_resolution=(1920,1080))
    #can change start_time to synch with the audio of the preview
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

    #TODO: add a transition clip with the parameter "transition"
    final_clip = concatenate_videoclips([guessing_clip, reveal_video],method="compose")
    #final_clip = final_clip.with_audio(audio_clip)
    final_clip = final_clip.with_effects([
        FadeIn(video_fade_in),
        FadeOut(video_fade_out)
    ])

    final_clip = final_clip.with_audio(audio_clip).with_effects([
        AudioFadeIn(audio_fade_in),
        AudioFadeOut(audio_fade_out)
    ])

    return final_clip, tmp.name

def assemble_video(
        clips: list,
        output_path: str,
        fps: int = 24
) -> None :
    """Assemble a list of different clips to make a video

    Parameters
    ----------
    clips : list
        a list of clips built by build_clips
    output_path : str
        the path to the output video file
    fps : int
        frames per second

    Returns
    -------
    None
    """
    print(output_path)
    print(type(output_path))
    final = concatenate_videoclips(clips)
    final.write_videofile(str(BASE_DIR / output_path), fps=fps)

