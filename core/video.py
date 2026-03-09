from moviepy import VideoClip, AudioFileClip, concatenate_videoclips
import numpy as np
from core.visuals import make_excerpt_frame, make_reveal_frame
from core.audio import AudioTrack, AudioSegment, BASE_DIR
import tempfile
import os


def build_clip(track: AudioTrack, excerpt_duration: int, reveal_duration: int):
    #a clip = one music with 10s of a excerpt + a 5s of a reveal of the artist and the song name
    #duration may vary
    total_duration = excerpt_duration + reveal_duration
    excerpt = track.get_excerpt(0, total_duration * 1000) #from ms to s
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    excerpt.export(tmp.name, format="mp3")
    tmp.close()

    def make_frame_excerpt(t):
        countdown = excerpt_duration - int(t)
        frame = make_excerpt_frame(countdown, 1, 1)
        return np.array(frame)

    def make_frame_reveal(t):
        frame = make_reveal_frame(track.artist, track.title)
        return np.array(frame)

    excerpt_clip = VideoClip(make_frame_excerpt, duration=excerpt_duration)
    audio_clip = AudioFileClip(tmp.name)
    excerpt_clip = excerpt_clip.with_audio(audio_clip)

    reveal_clip = VideoClip(make_frame_reveal, duration=reveal_duration)

    final_clip = concatenate_videoclips([excerpt_clip, reveal_clip])
    audio_clip = AudioFileClip(tmp.name)
    final_clip = final_clip.with_audio(audio_clip)

    return final_clip, tmp.name  # on retourne le nom pour nettoyer après

#test clip
#clip, tmp_name = build_clip(AudioTrack("data/music/Gorillaz - Feel Good Inc.mp3"), 10, 5)
#clip.write_videofile(str(BASE_DIR / "output/test2.mp4"), fps=30)
#os.unlink(tmp_name)  # nettoyage après export

def assemble_video(clips: list, output_path: str):
    #a video is composed of a list of subsequent clips
    final = concatenate_videoclips(clips)
    final.write_videofile(output_path, fps=24)

#test video
track1 = AudioTrack("data/music/Gorillaz - Feel Good Inc.mp3")
track2 = AudioTrack("data/music/Black Sabbath - Paranoid (Official Audio).mp3")
clip1, tmp1 = build_clip(track1, 10, 5)
clip2, tmp2 = build_clip(track2, 10, 5)

assemble_video([clip1, clip2], str(BASE_DIR / "output/test_final.mp4"))

os.unlink(tmp1)
os.unlink(tmp2)