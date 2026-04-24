import tkinter as tk
from tkinter import ttk
from core.database import get_genres, init_db

class GenresChecklist(ttk.Frame):
    """
    A scrollable checklist widget for selecting multiple genres.

    This widget displays a list of checkboxes inside a scrollable area,
    with optional "Select all" functionality.

    Parameters
    ----------
    master : widget, optional
        Parent widget.
    add_select_all_btn : bool, optional
        Whether to include a "Select all" checkbox at the top.
        Default is True.
    *args : tuple
        Additional positional arguments passed to ttk.Frame.
    **kwargs : dict
        Additional keyword arguments passed to ttk.Frame.

    Notes
    -----
    The scrollable behavior is implemented using a Tkinter Canvas
    containing a Frame. The canvas dynamically updates its scroll region
    and resizes the embedded frame to match its width.
    """

    def __init__(self, master=None, add_select_all_btn=True, selected_genres=[], *args, **kwargs):
        """
        Initialize the GenresChecklist widget.
        """
        super().__init__(master, *args, **kwargs)

        # Configure layout to allow full expansion
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Trying to get genre list from db
        list_choices = get_genres()
        if not list_choices:
            list_choices = ["Pop",
                            "Rap/ Hip Hop",
                            "Rock",
                            "Dance",
                            "R&B",
                            "Alternative",
                            "Electro",
                            "Chanson française",
                            "Reggae",
                            "Jazz",
                            "Metal",
                            "Soul & Funk",
                            "Blues",
                            "Latino"]


        # Store variables associated with each checkbox
        self._vars = []

        # Variable for "Select all" checkbox
        self._var_select_all = tk.IntVar()

        # =========================
        # Canvas + scrollbar
        # =========================
        # Canvas acts as a scrollable container
        self._canvas = tk.Canvas(self, highlightthickness=0)

        # Vertical scrollbar linked to the canvas
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)

        # Frame embedded inside the canvas
        self._scrollable_frame = ttk.Frame(self._canvas)

        # Create window inside canvas to host the frame
        self._canvas_window = self._canvas.create_window(
            (0, 0),
            window=self._scrollable_frame,
            anchor="nw"
        )

        # Ensure the embedded frame always matches the canvas width
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(self._canvas_window, width=e.width)
        )

        # Update scroll region whenever the content size changes
        self._scrollable_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")
            )
        )

        # Link scrollbar to canvas vertical scrolling
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # Layout canvas and scrollbar
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._scrollbar.grid(row=0, column=1, sticky="ns")

        # Ensure proper expansion behavior
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # =========================
        # Mouse wheel support
        # =========================
        # Enable scrolling when mouse enters the widget
        self._canvas.bind("<Enter>", self._bind_mousewheel)

        # Disable scrolling when mouse leaves the widget
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

        # =========================
        # Content initialization
        # =========================
        # Optional "Select all" checkbox
        if add_select_all_btn:
            self._add_select_all_row_btn()

        # Create one checkbox per genre
        for choice in list_choices:
            if choice in selected_genres:
                self._add_row(choice, default_val=True)
            else:
                self._add_row(choice, default_val=False)

    # =========================
    # Mouse wheel handling
    # =========================
    def _bind_mousewheel(self, event):
        """
        Bind mouse wheel events for scrolling.

        Supports Windows, macOS, and Linux.
        """
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        """
        Unbind mouse wheel events when cursor leaves the widget.
        """
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        """
        Handle mouse wheel scrolling.

        Parameters
        ----------
        event : tk.Event
            Mouse wheel event containing scroll direction and delta.
        """
        # Windows / macOS
        if hasattr(event, "delta") and event.delta:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # Linux
        elif event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")

    # =========================
    # UI construction
    # =========================
    def _add_select_all_row_btn(self):
        """
        Add the "Select all" checkbox at the top of the list.
        """
        frame_row = ttk.Frame(self._scrollable_frame)

        ttk.Checkbutton(
            frame_row,
            text="Select all",
            variable=self._var_select_all,
            command=self._toggle_all
        ).pack(anchor="w")

        frame_row.pack(fill="none", anchor="w")

    def _add_row(self, row_name, default_val=False):
        """
        Add a checkbox row for a given genre.

        Parameters
        ----------
        row_name : str
            Name of the genre to display.
        """
        frame_row = ttk.Frame(self._scrollable_frame)

        var_row = tk.IntVar()

        ttk.Checkbutton(
            frame_row,
            text=row_name,
            variable=var_row
        ).pack(anchor="w")

        frame_row.pack(fill="none", anchor="w")

        if default_val:
            var_row.set(1)
        # Store variable and associated label
        self._vars.append((var_row, row_name))

    # =========================
    # Logic
    # =========================
    def _toggle_all(self):
        """
        Toggle all checkboxes based on the "Select all" state.
        """
        value = self._var_select_all.get()
        for var, _ in self._vars:
            var.set(value)

    def get_selected_genres_list(self):
        """
        Retrieve the list of selected genres.

        Returns
        -------
        list of str
            Names of all selected genres.
        """
        return [name for var, name in self._vars if var.get() == 1]