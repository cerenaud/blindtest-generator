from pathlib import Path
import random
from core.audio import AudioTrack, AudioSegment, BASE_DIR
from moviepy import VideoClip, AudioFileClip, concatenate_videoclips
import numpy as np
from core.visuals import make_excerpt_frame, make_reveal_frame
from core.audio import AudioTrack, AudioSegment, BASE_DIR
import tempfile
import os
from core.video import build_clip  , assemble_video

def generate_blindtest(
    music_folder: str,
    output_path: str,
    nb_tracks: int = 10,
    excerpt_duration: int = 10,
    reveal_duration: int = 5,
        ) -> str:
    '''Scan data/music folder and generate blindtest video from it
    '''

    mp3_files = list((BASE_DIR / music_folder).glob("*.mp3")) #list of path for AudioTrack
    clips = []
    selected = random.sample(mp3_files, nb_tracks)  # nb_tracks fichiers sans répétition
    for mp3 in selected:
        track = AudioTrack(str(mp3))
        clip, tmp = build_clip(track, 10, 5)
        clips.append(clip)
    assemble_video(clips, output_path)


music_folder ="data/music"
output_path = "output/test_blindtest.mp4"
generate_blindtest(music_folder,output_path,3,10,5)

