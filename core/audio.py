from __future__ import annotations
import random
from pathlib import Path
from mutagen.id3 import ID3
from pydub import AudioSegment

BASE_DIR = Path(__file__).parent.parent  # go back from core/ to root


class AudioTrack:
    """ Create an audio track from a mp3 file.

    Initialize an AudioTrack from a local MP3 file.

    Reads ID3 metadata tags (title, artist) from the file.
    Falls back to the filename stem if tags are missing.

    Parameters
    ----------
    file_path : str
        Path to the MP3 file. Can be absolute or relative to the project root.

    Raises
    ------
    FileNotFoundError
        If the file does not exist at the given path.
    """
    def __init__(
            self,
            file_path: str
    ) -> None:
        path = Path(file_path)
        if path.is_absolute():
            self.path = path
        else:
            self.path = BASE_DIR / file_path

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
    def from_db(
            cls,
            db_row: tuple
    ) -> AudioTrack:
        """Create an AudioTrack instance from a database row.

        Alternative constructor to __init__, used when loading tracks
        from the SQLite database instead of reading ID3 tags.

        Parameters
        ----------
        db_row : tuple
            A row from the tracks table in the following order:
            (id, title, artist, album, genre, year, popularity, duration,
            preview_url, preview_path, deezer_id)

        Returns
        -------
        AudioTrack
            A new AudioTrack instance with metadata from the database.

        Raises
        ------
        ValueError
            If the MP3 file at preview_path cannot be loaded.
        """
        instance = cls.__new__(cls)
        instance.title = db_row[1]
        instance.artist = db_row[2]
        instance.album = db_row[3]
        instance.genre = db_row[4]
        instance.year = db_row[5]
        instance.popularity = db_row[6]
        instance.duration = db_row[7]
        instance.path = Path(db_row[9])
        instance.album_cover_path = db_row[11]
        try:
            instance.audio = AudioSegment.from_mp3(instance.path)
            instance.total_duration = len(instance.audio)
        except Exception:
            raise ValueError(f"Cannot load {instance.path}")
        return instance

    def get_excerpt(
            self,
            start_ms: int,
            duration_ms: int
    ) -> AudioSegment:
        """Get an excerpt from a song.

        Parameters
        ----------
        start_ms: int
            start from where to get the excerpt in a song in ms.
        duration_ms: int
            duration of the excerpt in ms.

        Returns
        -------
        :class: pydub.audio_segment
        """

        return self.audio[start_ms:start_ms + duration_ms]

    def get_random_excerpt(
            self,
            duration_ms: int
    ) -> AudioSegment:
        """Get a random excerpt from a song.

        Parameters
        ----------
        duration_ms: int
            duration of the excerpt in ms.

        Returns
        -------
        :class: pydub.audio_segment
        """

        max_start = self.total_duration - duration_ms
        start = random.randint(0, max_start)
        return self.audio[start:start + duration_ms]




