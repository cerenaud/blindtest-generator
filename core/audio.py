import random
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1
from pydub.playback import play
from pydub import AudioSegment
BASE_DIR = Path(__file__).parent.parent  # remonte de core/ vers la racine


class AudioTrack:
    def __init__(self, file_path: str):
        path = Path(file_path)
        if path.is_absolute():
            self.path = path
        else:
            self.path = BASE_DIR / file_path

        # metadonnees ID3
        try:
            tags = ID3(self.path)
            self.title = tags["TIT2"].text[0]
            self.artist = tags["TPE1"].text[0]
        except Exception:
            self.title = self.path.stem
            self.artist = "Unknown"

        self.audio = AudioSegment.from_mp3(self.path)
        self.total_duration = len(self.audio)

    @classmethod
    def from_db(cls, db_row: tuple):
        instance = cls.__new__(cls)
        instance.title = db_row[1]
        instance.artist = db_row[2]
        instance.path = Path(db_row[7])  # preview_path
        instance.audio = AudioSegment.from_mp3(instance.path)
        instance.total_duration = len(instance.audio)
        return instance

    def get_excerpt(self, start_ms: int, duration: int) -> AudioSegment:
        return self.audio[start_ms:start_ms + duration]

    def get_random_excerpt(self, duration: int)-> AudioSegment:
        max_start = self.total_duration - duration
        start = random.randint(0, max_start)
        return self.audio[start:start + duration]




