# Blindtest Generator V1


The project can:

- create and fill a local SQLite database with tracks from the Deezer API;
- download Deezer preview MP3 files and album covers;
- generate a blindtest video with an intro, guessing rounds, reveal rounds, and an outro.

The local database is stored here:

```text
data/blindtest.db
```

## Stack

- Python 3.12
- SQLite
- Deezer API
- MoviePy
- pydub
- yt-dlp
- Pillow
- mutagen
- requests
- langchain
- python-dotenv
- yt-dlp

## Installation

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install `ffmpeg` and make sure it is available from the terminal:

```bash
ffmpeg -version
```

One functions also use OpenAI through `ai/agents.py`. Make sure your API key is available in your environment or `.env` file. You will only need a free API key.

## Creating music database

Execute the functions in main.py, it will guide you for creating and filling the database.


## Generate Blindtest

To generate a blindtest, you will need: 
- an intro song and background video
- An outro song and background video
- a reveal and guessing background video
You will need to fulfill the path in these variables:
```python
    intro_path = "path/to/intro_video.mp4" #path to the intro background video
    intro_song = "path/to/intro_song.mp3"
    outro_path = "path/to/outro_video.mp4" #path to the outro background video
    outro_song = "path/to/outro_video.mp3"
    guessing_background = "path/to/guessing_background_video.mp4"
    reveal_background = "path/to/reveal_background_video.mp4"
```

You can then generate different Blindtest by genre,subgenre, max & min year, max & min popularity and number of tracks per blindtest. (More info in generate_blindtest_iterative docstring).

```python
from core.generator import generate_blindtest_iterative

generate_blindtest_iterative(
    output_path="output/blindtest_rock.mp4",
    intro_text="Rock Blindtest",
    intro_background=intro_background,
    intro_song=intro_song,
    outro_background=outro_background,
    outro_song=outro_song,
    nb_tracks=50,
    guessing_duration=10,
    reveal_duration=5,
    genre="Rock",
    sub_genre = "classic_rock"
    min_year=1970,
    max_year=2026
)
```
There are currently 6 genre of music:
- Rock
- Pop
- Rap
- Chanson française / french music
- Electro
- Metal

You can search every subgenre of a genre in genre.py

Generate without a genre filter:

```python
from core.generator import generate_blindtest_iterative

generate_blindtest_iterative(
    output_path="output/blindtest_mix.mp4",
    intro_text="Mixed Blindtest",
    intro_background=intro_background,
    intro_song=intro_song,
    outro_background=outro_background,
    outro_song=outro_song,
    nb_tracks=50,
    guessing_duration=10,
    reveal_duration=5,
)
```

## Notes

- `download_all_previews()` must be run before generating a blindtest because `get_tracks()` only selects tracks with a local `preview_path`.
- `import_by_genre()` filters tracks using album genres returned by Deezer, so it can import fewer tracks than requested.
- Temporary video files are created in `data/tmp_blindtest` and removed after generation.
