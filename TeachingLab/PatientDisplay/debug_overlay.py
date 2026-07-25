import tkinter as tk


class DebugOverlay:
    """
    Transparent fullscreen canvas drawn over the monitored monitor.
    Shows each ROI as a coloured rectangle with live current/baseline/diff values.
    Green = idle, Red = active.
    """

    def __init__(self, root):
        self._root = root
        self._win = None
        self._canvas = None

    def show(self, left, top, width, height):
        if self._win:
            return
        self._win = tk.Toplevel(self._root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.attributes("-transparentcolor", "black")
        self._win.geometry(f"{width}x{height}+{left}+{top}")
        self._canvas = tk.Canvas(self._win, bg="black", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

    def hide(self):
        if self._win:
            self._win.destroy()
            self._win = None
            self._canvas = None

    def update(self, roi_data):
        if not self._canvas:
            return
        self._canvas.delete("roi")
        for r in roi_data:
            x, y, w, h = r["x"], r["y"], r["w"], r["h"]
            color = "#FF4444" if r["active"] else "#44FF44"
            self._canvas.create_rectangle(
                x, y, x + w, y + h,
                outline=color, width=3, fill="", tags="roi",
            )
            label = (
                f"{r['id']}  "
                f"now={r['current']:.0f}  "
                f"peak={r['peak']:.0f}  "
                f"trigger>{r['threshold']}"
            )
            self._canvas.create_text(
                x + 4, y + 4,
                anchor="nw", text=label,
                fill=color, font=("Arial", 10, "bold"),
                tags="roi",
            )
