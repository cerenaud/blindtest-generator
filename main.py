from core.database import init_db, import_by_genre, import_movies_series, download_all_previews, download_all_album_covers, \
    download_all_youtube_videos
from core.generator import generate_blindtest_iterative

if __name__ == "__main__":
    #first time launching
    init_db()

    #importing music by genre to fill the database massively and correct
    #it will import 3 tracks per artist from a pre-filled selection of artist to ensure genre validity
    import_by_genre("rock",20) #max number of tracks to import for this genre : 1110
    import_by_genre("pop",20) #max : 774
    import_by_genre("rap",20) #max : 762
    import_by_genre("chanson_fr",20) #max : 744
    import_by_genre("electro",20) #max : 891
    import_by_genre("metal",20) #max : 858
    import_by_genre("country",20) #max : 204
    import_by_genre("funk_soul",20) #max : 222

    #importing movies/series themes: 1 track per query entry (see genres.py), not 3 per artist
    import_movies_series("movies",20) #max : 419
    import_movies_series("series",20) #max : 140

    #downloading song previews and album covers for all music in the database.
    download_all_previews()
    download_all_album_covers()

    #optionnal
    download_all_youtube_videos()

    #You'll need to fill the path to your own songs and background video to generate a blindtest
    intro_path = "" #path to the intro background video
    intro_song = ""
    outro_path = "" #path to the outro background video
    outro_song = ""
    guessing_background = ""
    reveal_background = ""

    #generate_blindtest_iterative(
    #     "output/Blindtest.mp4",
    #     intro_text = "All genre",
    #     nb_tracks= 15 ,
    #     guessing_duration= 10,
    #     reveal_duration= 5,
    #     intro_background =intro_path,
    #     intro_song =intro_song,
    #     outro_background =outro_path,
    #     outro_song =outro_song
    #)