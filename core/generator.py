from pathlib import Path
import random
from core.audio import AudioTrack, AudioSegment, BASE_DIR
from moviepy import VideoClip, AudioFileClip, concatenate_videoclips
from core.database import clean_db

from core.database import get_tracks
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
    clean_db()
    '''
    mp3_files = list((BASE_DIR / music_folder).glob("*.mp3")) #list of path for AudioTrack
    clips = []
    selected = random.sample(mp3_files, nb_tracks)  # nb_tracks fichiers sans répétition
    track_number_counter = 0
    for mp3 in selected:
        track_number_counter += 1
        track = AudioTrack(str(mp3))
        clip, tmp = build_clip(track, 10, 5,track_number_counter,nb_tracks)
        clips.append(clip)
    assemble_video(clips, output_path)'''

    #nouvellle facçon a test:
    mp3_files = get_tracks(nb_tracks)
    clips = []
    track_number_counter = 1
    for i in range(len(mp3_files)):
        try:
            track = AudioTrack.from_db(mp3_files[i])
            clip, tmp = build_clip(track, excerpt_duration, reveal_duration, track_number_counter, nb_tracks)
            clips.append(clip)
            track_number_counter += 1

        except ValueError as e:
            print(f"Skipping track: {e}")

    assemble_video(clips, output_path)
    return output_path

# music_folder ="data/music"
# output_path = "output/test_blindtest_5.mp4"
# generate_blindtest(music_folder,output_path,25,10,5)
#
