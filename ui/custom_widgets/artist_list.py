import tkinter as tk
from tkinter import ttk


class ArtistList(ttk.Frame):
    """
    A Tkinter widget for entering and retrieving a list of artist names.

    This component provides a labeled text area with a vertical scrollbar,
    allowing users to input multiple lines (one artist per line).

    Parameters
    ----------
    master : widget, optional
        Parent widget.
    label_name : str, optional
        Label displayed above the text area. Default is "Artist".
    displayed_lines_numbers : int, optional
        Number of visible lines in the text area. Default is 5.
    *args : tuple
        Additional positional arguments passed to ttk.Frame.
    **kwargs : dict
        Additional keyword arguments passed to ttk.Frame.
    """

    def __init__(self, master=None, label_name="Artist", displayed_lines_numbers=5, *args, **kwargs):
        """
        Initialize the ArtistList widget.
        """
        super().__init__(master, *args, **kwargs)

        # Configure column expansion to allow horizontal resizing
        self.columnconfigure(0, weight=1)

        # =========================
        # Label section
        # =========================
        frame_label = ttk.Frame(self)
        frame_label.grid(row=0, column=0, sticky="w")

        # Display the label name
        ttk.Label(frame_label, text=label_name).pack(anchor="w")

        # =========================
        # Text area container
        # =========================
        frame_text_area = ttk.Frame(self)
        frame_text_area.grid(row=1, column=0, sticky="nsew")

        # =========================
        # Scrollbar
        # =========================
        scrollbar = ttk.Scrollbar(frame_text_area, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # =========================
        # Text widget
        # =========================
        self._text_area = tk.Text(
            frame_text_area,
            height=displayed_lines_numbers,
            wrap="word",
            yscrollcommand=scrollbar.set
        )

        # Place text widget; horizontal expansion disabled to control layout width
        self._text_area.pack(side=tk.LEFT, fill=tk.X, expand=False)

        # Link scrollbar to text widget scrolling
        scrollbar.config(command=self._text_area.yview)

    def get_list(self):
        """
        Retrieve the list of entered artists.

        Returns
        -------
        list of str
            A list of non-empty, trimmed strings corresponding to each line
            entered in the text area.
        """
        return [x.strip() for x in self._text_area.get(1.0, tk.END).split("\n") if x.strip() != ""]