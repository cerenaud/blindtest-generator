import tkinter as tk
from tkinter import ttk, filedialog


class PathSelector(ttk.Frame):
    """
    A reusable Tkinter widget for selecting a file or directory.

    Features:
    - Optional label describing the expected path
    - Entry field displaying the selected path
    - Browse button to open a file/directory dialog
    """

    def __init__(
        self,
        parent,
        label_text=None,
        select_type="file",  # "file" or "directory"
        filetypes=(("All files", "*.*"),),
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.select_type = select_type
        self.filetypes = filetypes

        # Tkinter variable to store the selected path
        self.path_var = tk.StringVar()

        # Optional label displayed above the selector
        if label_text:
            self.label = ttk.Label(self, text=label_text)
            self.label.pack(anchor="w", pady=(0, 2))

        # Container for Entry + Button
        inner_frame = ttk.Frame(self)
        inner_frame.pack(fill="x", expand=True)

        # Entry widget to display/edit the path
        self.entry = ttk.Entry(inner_frame, textvariable=self.path_var)
        self.entry.pack(side="left", fill="x", expand=True)

        # Button to open file/directory selection dialog
        self.button = ttk.Button(
            inner_frame,
            text="Browse...",
            command=self._browse
        )
        self.button.pack(side="left", padx=(5, 0))

    def _browse(self):
        """Open the appropriate dialog depending on select_type."""
        if self.select_type == "file":
            path = filedialog.askopenfilename(filetypes=self.filetypes)
        elif self.select_type == "directory":
            path = filedialog.askdirectory()
        else:
            raise ValueError("select_type must be 'file' or 'directory'")

        # Update the entry only if a path was selected
        if path:
            self.path_var.set(path)

    def get(self):
        """Return the currently selected path."""
        return self.path_var.get()

    def set(self, value):
        """Set the path programmatically."""
        self.path_var.set(value)


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("PathSelector Demo")

    # File selector example
    file_selector = PathSelector(
        root,
        label_text="Select a file:",
        select_type="file",
        filetypes=(("Images", "*.png;*.jpg"), ("All files", "*.*"))
    )
    file_selector.pack(fill="x", padx=10, pady=10)

    # Directory selector example
    dir_selector = PathSelector(
        root,
        label_text="Select a directory:",
        select_type="directory"
    )
    dir_selector.pack(fill="x", padx=10, pady=10)

    def print_values():
        print("File:", file_selector.get())
        print("Directory:", dir_selector.get())

    ttk.Button(root, text="Print values", command=print_values).pack(pady=10)

    root.mainloop()