import os
import pickle
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from ui.custom_widgets.genres_checklist import GenresChecklist
from ui.custom_widgets.artist_list import ArtistList
from ui.custom_widgets.path_selector import PathSelector
from core.generator import generate_blindtest


MAINWINDOW_WIDTH = 600
MAINWINDOW_HEIGHT = 400

# Root directory of the project
ROOT_DIR = Path(__file__).parent.parent

# Path to the saved configuration file
PATH_TO_PICKLED_PARAMS = ROOT_DIR / "ui" / "ui_config" / "params_save.pickle"


class IHMBlindTestCreation(tk.Tk):
    """
    Main application window for configuring and generating a blind test.

    This GUI allows users to:
    - Select input and output directories
    - Configure game settings (number of tracks, durations, year range)
    - Define included and excluded artists
    - Choose music genres
    - Launch the blind test generation process

    Layout
    ------
    The interface is divided into two main sections:
    - Left panel: configuration and filters
    - Right panel: genre selection and action button

    Notes
    -----
    The layout relies on a grid system with weighted columns
    to ensure responsive resizing.
    """

    def __init__(self):
        """
        Initialize the main window and all UI components.

        This includes:
        - Loading previously saved configuration (if available)
        - Creating and arranging all widgets
        - Applying default values
        """
        super().__init__()

        # ======================
        # Window configuration
        # ======================
        self.title('Blindtest creation')

        # Set initial and minimum window size
        self.geometry(f"{MAINWINDOW_WIDTH}x{MAINWINDOW_HEIGHT}")
        self.minsize(MAINWINDOW_WIDTH, MAINWINDOW_HEIGHT)

        current_year = datetime.now().year

        # Default configuration values
        # These will be overridden if a saved configuration is found
        default_config = {
            "music_folder": "",
            "output_folder": "",
            "tracks_qty": 20,
            "guessing_duration_s": 20,
            "reveal_duration_s": 5,
            "min_year": 1980,
            "max_year": current_year,
            "list_included_artists": [],
            "list_excluded_artists": [],
            "selected_genres": []
        }

        # Attempt to load previously saved configuration
        # If loading fails, fallback to default values
        if os.path.exists(PATH_TO_PICKLED_PARAMS):
            try:
                with open(PATH_TO_PICKLED_PARAMS, "rb") as f:
                    saved_config = pickle.load(f)
                    default_config.update(saved_config)
            except Exception:
                # Silently ignore corrupted or incompatible config files
                pass

        # ======================
        # Global layout
        # ======================
        # Two-column layout:
        # - Left: main configuration (takes more space)
        # - Right: genres and actions (takes less space)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)

        # Validation command for integer-only inputs
        vint = (self.register(self._validate_int), "%P")

        #####################
        # LEFT PANEL: FILTERS & SETTINGS
        #####################
        self.filters = ttk.LabelFrame(self, text="Filters", padding=10)
        self.filters.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        self.filters.columnconfigure(0, weight=1)

        # Music folder selection
        self._path_music_folder = PathSelector(
            self.filters,
            label_text="Music Folder:",
            select_type="directory"
        )
        self._path_music_folder.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self._path_music_folder.set(default_config["music_folder"])

        # Output directory selection
        self._output_path = PathSelector(
            self.filters,
            label_text="Output Folder:",
            select_type="directory"
        )
        self._output_path.grid(row=1, column=0, sticky="w", pady=(0, 5))
        self._output_path.set(default_config["output_folder"])

        # Number of tracks
        f_tracks_qty = ttk.Frame(self.filters)
        f_tracks_qty.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(f_tracks_qty, text="Number of Tracks:").grid(row=0, column=0, sticky="w")
        self._tracks_qty = ttk.Spinbox(f_tracks_qty, from_=1, width=5)
        self._tracks_qty.grid(row=0, column=1, sticky="w", padx=5)
        self._tracks_qty.set(default_config["tracks_qty"])

        # Extract duration (guessing phase)
        f_extract_duration = ttk.Frame(self.filters)
        f_extract_duration.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(f_extract_duration, text="Extract Duration (seconds):").grid(row=0, column=0, sticky="w")
        self._extract_duration = ttk.Spinbox(f_extract_duration, from_=1, to=10000, width=5)
        self._extract_duration.grid(row=0, column=1, sticky="w", padx=5)
        self._extract_duration.set(default_config["guessing_duration_s"])

        # Reveal duration
        f_reveal_duration = ttk.Frame(self.filters)
        f_reveal_duration.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(f_reveal_duration, text="Reveal Duration (seconds):").grid(row=0, column=0, sticky="w")
        self._reveal_duration = ttk.Spinbox(f_reveal_duration, from_=1, to=10000, width=5)
        self._reveal_duration.grid(row=0, column=1, sticky="w", padx=5)
        self._reveal_duration.set(default_config["reveal_duration_s"])

        # Year range filter
        f_years = ttk.Frame(self.filters)
        f_years.grid(row=5, column=0, sticky="ew", pady=(0, 10))

        f_years.columnconfigure(1, weight=0)
        f_years.columnconfigure(3, weight=2)

        ttk.Label(f_years, text="Year Range:").grid(row=0, column=0, sticky="w")

        self._min_year = ttk.Spinbox(f_years, from_=0, to=current_year, width=5)
        self._min_year.grid(row=0, column=1, sticky="w", padx=5)
        self._min_year.set(default_config["min_year"])

        ttk.Label(f_years, text="-").grid(row=0, column=2, sticky="w")

        self._max_year = ttk.Spinbox(f_years, from_=0, to=current_year, width=5)
        self._max_year.grid(row=0, column=3, sticky="w", padx=5)
        self._max_year.set(default_config["max_year"])

        # Included artists list
        self.artists = ArtistList(self.filters, "Included Artists:")
        self.artists.grid(row=6, column=0, sticky="nsew", pady=5)

        # Excluded artists list
        self.artists_excluded = ArtistList(self.filters, "Excluded Artists:")
        self.artists_excluded.grid(row=7, column=0, sticky="nsew", pady=5)

        #####################
        # RIGHT PANEL (TOP): GENRE SELECTION
        #####################
        self.genres = ttk.LabelFrame(self, text="Genres", padding=10)
        self.genres.columnconfigure(0, weight=1)
        self.genres.rowconfigure(0, weight=1)
        self.genres.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Genre selection widget
        self._genre_checklist = GenresChecklist(
            self.genres,
            selected_genres=default_config["selected_genres"]
        )
        self._genre_checklist.grid(row=0, column=0, sticky="nsew")

        #####################
        # RIGHT PANEL (BOTTOM): ACTIONS
        #####################
        self.actions = ttk.LabelFrame(self, text="Actions", padding=10)
        self.actions.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 10))

        # Button to start blind test generation
        ttk.Button(
            self.actions,
            width=40,
            text="Create Blind Test",
            command=self.create_blindtest
        ).pack(fill="x")

        # ======================
        # Final layout adjustment
        # ======================
        self.update_idletasks()
        self.geometry(f"{MAINWINDOW_WIDTH}x{self.winfo_reqheight()}")

    #####################
    # LOGIC
    #####################
    def get_blindtest_parameters(self, save_parameters_next_instance=False):
        """
        Collect all user-defined parameters from the UI.

        Parameters
        ----------
        save_parameters_next_instance : bool, optional
            If True, the current configuration is saved to disk
            and reloaded automatically on next application launch.

        Returns
        -------
        dict
            A dictionary containing all parameters required
            to generate the blind test.
        """
        blindtest_parameters = {
            "music_folder": self._path_music_folder.get(),
            "output_folder": self._output_path.get(),
            "tracks_qty": self._tracks_qty.get(),
            "guessing_duration_s": self._extract_duration.get(),
            "reveal_duration_s": self._reveal_duration.get(),
            "min_year": self._min_year.get(),
            "max_year": self._max_year.get(),
            "list_included_artists": self.artists.get_list(),
            "list_excluded_artists": self.artists_excluded.get_list(),
            "selected_genres": self._genre_checklist.get_selected_genres_list()
        }

        # Optionally persist parameters for next session
        if save_parameters_next_instance:
            try:
                os.makedirs(os.path.dirname(PATH_TO_PICKLED_PARAMS), exist_ok=True)
                with open(PATH_TO_PICKLED_PARAMS, "wb") as file:
                    pickle.dump(blindtest_parameters, file)
            except Exception as e:
                print(f"Failed to save parameters: {e}")

        return blindtest_parameters

    def create_blindtest(self):
        """
        Generate the blind test using the current configuration.

        This method:
        - Retrieves all parameters from the UI
        - Saves them for future sessions
        - Calls the core generation logic
        """
        params = self.get_blindtest_parameters(save_parameters_next_instance=True)

        generate_blindtest(
            music_folder=params["music_folder"],
            output_path=params["output_folder"],
            nb_tracks=params["tracks_qty"],
            guessing_duration=params["guessing_duration_s"],
            reveal_duration=params["reveal_duration_s"],
            genre=params["selected_genres"],
            min_year=params["min_year"],
            max_year=params["max_year"],
        )

    def _validate_int(self, new_value):
        """
        Ensure that the input contains only numeric characters.

        Allows empty input so the user can edit the field freely.

        Parameters
        ----------
        new_value : str
            The proposed new value of the entry field.

        Returns
        -------
        bool
            True if valid, False otherwise.
        """
        if new_value == "":
            return True
        return new_value.isdigit()