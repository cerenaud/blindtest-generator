from core.audio import AudioTrack
import pytest

def test_audio_loading():
    track = AudioTrack("data/music/Gorillaz - Feel Good Inc.mp3")
    assert track.total_duration > 0

    assert track.title is not None
    assert isinstance(track.title, str)

    assert track.artist is not None
    assert isinstance(track.artist, str)

def test_get_excerpt():
    track = AudioTrack("data/music/Gorillaz - Feel Good Inc.mp3")
    excerpt = track.get_excerpt(0, 10000)
    assert len(excerpt) == 10000

def test_get_random_excerpt():
    track = AudioTrack("data/music/Gorillaz - Feel Good Inc.mp3")
    random_excerpt = track.get_random_excerpt(10000)
    assert len(random_excerpt) == 10000

def test_file_not_found():
    with pytest.raises(Exception):
        track = AudioTrack("data/music/fichier_inexistant.mp3")