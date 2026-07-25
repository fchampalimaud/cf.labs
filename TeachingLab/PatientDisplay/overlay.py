import threading
import tkinter as tk

# Pure black is the transparent key — every black pixel becomes see-through.
_TRANSPARENT = "black"
_PANEL_BG = "black"   # same as _TRANSPARENT → panel is invisible
_TEXT_FG = "#FF0000"  # red digits


class Overlay:
    """
    Full-screen transparent always-on-top window.
    Shows a red panel in the centre with the current cabinet label.
    Cycles through active cabinets once per display_interval_ms.
    """

    def __init__(self, root, display_interval_ms=1000, relx=0.5, rely=0.5, font_size=180, sub_font_size=22, sub_gap=0):
        self._active = True
        self._interval = display_interval_ms
        self._relx = relx
        self._rely = rely
        self._lock = threading.Lock()
        self._cabinets: list[str] = []
        self._index = 0

        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.attributes("-transparentcolor", _TRANSPARENT)
        self.top.configure(bg=_TRANSPARENT)

        sw = self.top.winfo_screenwidth()
        sh = self.top.winfo_screenheight()
        self.top.geometry(f"{sw}x{sh}+0+0")

        self._panel = tk.Frame(self.top, bg=_PANEL_BG)

        self._lbl_main = tk.Label(
            self._panel,
            text="",
            font=("Arial", font_size, "bold"),
            fg=_TEXT_FG,
            bg=_PANEL_BG,
        )
        self._lbl_main.pack()

        self._lbl_sub = tk.Label(
            self._panel,
            text="",
            font=("Arial", sub_font_size, "bold"),
            fg=_TEXT_FG,
            bg=_PANEL_BG,
        )
        self._lbl_sub.pack(pady=(max(sub_gap, 0), 0))

        self._panel_visible = False
        self._cycle()
        self._keep_on_top()

    # ------------------------------------------------------------------
    # Public API (called from any thread via root.after in main.py)
    # ------------------------------------------------------------------

    def update(self, cabinet_list: list[str]):
        with self._lock:
            # Try to keep showing the same cabinet if it's still active
            current = self._cabinets[self._index % len(self._cabinets)] if self._cabinets else None
            self._cabinets = list(cabinet_list)
            if current in self._cabinets:
                self._index = self._cabinets.index(current)
            else:
                self._index = 0

    def set_position(self, relx, rely):
        self._relx = relx
        self._rely = rely
        if self._panel_visible:
            self._panel.place(relx=self._relx, rely=self._rely, anchor="center")

    def set_font_size(self, size):
        self._lbl_main.config(font=("Arial", size, "bold"))

    def set_sub_font_size(self, size):
        self._lbl_sub.config(font=("Arial", size, "bold"))

    def set_sub_gap(self, gap):
        self._lbl_sub.pack_configure(pady=(max(gap, 0), 0))

    def hide(self):
        self._active = False
        self.top.destroy()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cycle(self):
        if not self._active:
            return
        with self._lock:
            if self._cabinets:
                self._index %= len(self._cabinets)
                label = self._cabinets[self._index]
                count = len(self._cabinets)
                self._lbl_main.config(text=label)
                self._lbl_sub.config(
                    text=f"{self._index + 1} / {count}" if count > 1 else ""
                )
                self._index += 1
                if not self._panel_visible:
                    self._panel.place(relx=self._relx, rely=self._rely, anchor="center")
                    self._panel_visible = True
            else:
                if self._panel_visible:
                    self._panel.place_forget()
                    self._panel_visible = False

        self.top.after(self._interval, self._cycle)

    def _keep_on_top(self):
        if not self._active:
            return
        self.top.lift()
        self.top.attributes("-topmost", True)
        self.top.after(500, self._keep_on_top)
