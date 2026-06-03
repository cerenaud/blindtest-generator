# Blindtest Generator

Temporary README for the blindtest video generator.

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

## Installation

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install `ffmpeg` and make sure it is available from the terminal:

```bash
ffmpeg -version
```

Some functions also use OpenAI through `ai/agents.py`. If you use those parts, make sure your API key is available in your environment or `.env` file.

## Database Creation And Import

Example snippet to create the database, import tracks, and download the required assets:

```python
from core.database import (
    init_db,
    import_by_genre,
    import_charts,
    import_by_artist,
    search_and_import,
    download_all_previews,
    download_all_album_covers,
    clean_db,
)

# 1. Create the SQLite database and table.
init_db()

# 2. Import tracks from Deezer.
import_by_genre(152, 500)      # Rock
import_by_genre(132, 300)      # Pop
import_by_genre(116, 250)      # Rap/Hip Hop
import_by_genre(106, 200)      # Electro
import_by_genre(52, 300)       # French songs

# Optional imports.
import_charts(100)             # Global Deezer charts
import_by_artist(27, 50)       # Top tracks for one Deezer artist ID
search_and_import("queen rock", 100)

# 3. Download local files used by the blindtest generator.
download_all_previews()
download_all_album_covers()

# 4. Clean missing or corrupted preview paths.
clean_db()
```

Useful Deezer genre IDs:

```text
132 : Pop
116 : Rap/Hip Hop
152 : Rock
113 : Dance
165 : R&B
85  : Alternative
106 : Electro
52  : Chanson française
144 : Reggae
129 : Jazz
464 : Metal
169 : Soul & Funk
153 : Blues
197 : Latino
```

Quick database checks:

```python
import sqlite3

con = sqlite3.connect("data/blindtest.db")
cur = con.cursor()

print(cur.execute("""
    SELECT genre, COUNT(*)
    FROM tracks
    GROUP BY genre
    ORDER BY COUNT(*) DESC
""").fetchall())

print(cur.execute("""
    SELECT genre, COUNT(*), SUM(preview_path IS NOT NULL)
    FROM tracks
    GROUP BY genre
    ORDER BY COUNT(*) DESC
""").fetchall())

con.close()
```

## Generate Blindtest

Example snippet to generate a blindtest video:

```python
from core.generator import generate_blindtest_iterative

intro_background = "data/backgrounds/black_yellow_30fps.mp4"
intro_song = "data/backgrounds/Watercolour - Pendulum [HQ].mp3"
outro_background = "data/backgrounds/soft_flow_pastel_30fps.mp4"
outro_song = "data/backgrounds/Nujabes - flowers [Official Audio].mp3"

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
    min_year=1970,
    max_year=2026,
)
```

Generate without a genre filter:

```python
from core.generator import generate_blindtest_iterative

generate_blindtest_iterative(
    output_path="output/blindtest_mix.mp4",
    intro_text="Mixed Blindtest",
    intro_background="data/backgrounds/black_yellow_30fps.mp4",
    intro_song="data/backgrounds/Watercolour - Pendulum [HQ].mp3",
    outro_background="data/backgrounds/soft_flow_pastel_30fps.mp4",
    outro_song="data/backgrounds/Nujabes - flowers [Official Audio].mp3",
    nb_tracks=50,
    guessing_duration=10,
    reveal_duration=5,
)
```

## Notes

- `download_all_previews()` must be run before generating a blindtest because `get_tracks()` only selects tracks with a local `preview_path`.
- `import_by_genre()` filters tracks using album genres returned by Deezer, so it can import fewer tracks than requested.
- Temporary video files are created in `data/tmp_blindtest` and removed after generation.
