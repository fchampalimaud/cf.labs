"""
Patient Display Monitor — launcher window.
"""

import ctypes
import sys

# DPI awareness must be set before Tk measures the screen
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# ── Splash (shown immediately, before heavy imports) ─────────────────────────
import tkinter as tk
from tkinter import ttk, messagebox

_root = tk.Tk()
_root.withdraw()

_splash = tk.Toplevel(_root)
_splash.overrideredirect(True)
_splash.attributes("-topmost", True)
_splash.configure(bg="#0d1b2a")

_SW = _root.winfo_screenwidth()
_SH = _root.winfo_screenheight()
_W, _H = 440, 210
_splash.geometry(f"{_W}x{_H}+{(_SW - _W) // 2}+{(_SH - _H) // 2}")

tk.Label(
    _splash, text="Patient Display Monitor",
    font=("Arial", 18, "bold"), fg="white", bg="#0d1b2a",
).pack(pady=(30, 4))
tk.Label(
    _splash, text="Hospital Cabinet Alert System",
    font=("Arial", 10), fg="#90caf9", bg="#0d1b2a",
).pack()

_prog_text = tk.StringVar(value="Starting…")
tk.Label(
    _splash, textvariable=_prog_text,
    font=("Arial", 9), fg="#78909c", bg="#0d1b2a",
).pack(pady=(18, 4))

_bar = ttk.Progressbar(_splash, length=360, mode="determinate", maximum=100)
_bar.pack(pady=(0, 20))
_splash.update()


def _progress(pct: int, text: str):
    _bar["value"] = pct
    _prog_text.set(text)
    _splash.update()


# ── Heavy imports with progress updates ───────────────────────────────────────
_progress(10, "Loading screen capture…")
import mss                                               # noqa: E402

_progress(25, "Loading image processing…")
import numpy                                             # noqa: E402  # pre-warm for monitor.py

_progress(40, "Loading keyboard hook…")
import keyboard                                          # noqa: E402

_progress(55, "Loading configuration…")
import log as _log                                       # noqa: E402
import config                                            # noqa: E402

_progress(70, "Loading components…")
from monitor import ScreenMonitor                        # noqa: E402
from overlay import Overlay                              # noqa: E402
from debug_overlay import DebugOverlay                   # noqa: E402
from setup_tool import SetupWindow                       # noqa: E402

_progress(85, "Building interface…")

logger = _log.get()


def _handle_exception(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))


sys.excepthook = _handle_exception

_HOTKEY = "ctrl+shift+h"


# ── Main application ──────────────────────────────────────────────────────────
class App:
    def __init__(self):
        self.root = _root
        self.root.title("Patient Display")
        self.root.attributes("-topmost", True)

        cfg = config.load()
        x, y = cfg.get("window_x", 100), cfg.get("window_y", 100)

        self._monitor = None
        self._overlay = None
        self._debug_overlay = None
        self._running = False
        self._debug_on = False
        self._save_pos_job = None
        self._visible = True

        logger.info("App started")
        self._build_ui(cfg)

        self.root.update_idletasks()
        w = 420
        h = self.root.winfo_reqheight()
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.resizable(False, False)

        _progress(100, "Ready")
        # Close splash then reveal main window shortly after mainloop starts
        self.root.after(400, _splash.destroy)
        self.root.after(450, self.root.deiconify)

        self.root.bind("<Configure>", self._on_configure)
        try:
            keyboard.add_hotkey(_HOTKEY, self._toggle_window)
            logger.info("Global hotkey registered: %s", _HOTKEY)
        except Exception as e:
            logger.warning("Hotkey registration failed: %s", e)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self, cfg):
        tk.Label(
            self.root,
            text="Patient Display Monitor",
            font=("Arial", 12, "bold"),
        ).pack(pady=(10, 0))
        tk.Label(
            self.root,
            text="Ctrl+Shift+H  —  hide / show",
            font=("Arial", 8),
            fg="gray",
        ).pack(pady=(0, 6))

        sliders_frame = tk.LabelFrame(self.root, text="Display Settings", padx=8, pady=6)
        sliders_frame.pack(fill="x", padx=12, pady=(0, 8))

        self._disp_x    = tk.IntVar(value=int(cfg.get("display_x", 0.5) * 100))
        self._disp_y    = tk.IntVar(value=int(cfg.get("display_y", 0.5) * 100))
        self._font_size = tk.IntVar(value=cfg.get("font_size", 180))
        self._sub_font  = tk.IntVar(value=cfg.get("sub_font_size", 22))
        self._sub_gap   = tk.IntVar(value=cfg.get("sub_gap", 0))

        self._add_slider(sliders_frame, "X pos %",   self._disp_x,    0,   100, 0)
        self._add_slider(sliders_frame, "Y pos %",   self._disp_y,    0,   100, 1)
        self._add_slider(sliders_frame, "Font size", self._font_size, 30,   400, 2)
        self._add_slider(sliders_frame, "Sub size",  self._sub_font,   6,   100, 3)
        self._add_slider(sliders_frame, "Sub gap",   self._sub_gap,    0,   200, 4)

        btn_row = tk.Frame(self.root)
        btn_row.pack(pady=(0, 8))

        tk.Button(
            btn_row, text="Setup ROIs", command=self._open_setup, width=11,
        ).pack(side="left", padx=4)

        self._debug_btn = tk.Button(
            btn_row, text="Debug ROIs", command=self._toggle_debug, width=11,
        )
        self._debug_btn.pack(side="left", padx=4)

        self._start_stop_btn = tk.Button(
            btn_row,
            text="▶  Start",
            command=self._toggle_start_stop,
            width=11,
            bg="#2e7d32",
            fg="white",
            font=("Arial", 9, "bold"),
        )
        self._start_stop_btn.pack(side="left", padx=4)

        tk.Label(self.root, text="Active ROIs:", font=("Arial", 8, "bold")).pack()
        self._active_var = tk.StringVar(value="—")
        tk.Label(
            self.root,
            textvariable=self._active_var,
            fg="#CC0000",
            font=("Arial", 9),
            wraplength=400,
        ).pack(pady=(0, 8))

    def _add_slider(self, parent, label, variable, from_, to, row):
        tk.Label(parent, text=label, anchor="w", width=9).grid(
            row=row, column=0, sticky="w", pady=2
        )
        val_str = tk.StringVar(value=str(variable.get()))
        def on_change(val, vs=val_str):
            vs.set(str(int(float(val))))
            self._save_display_settings()
        tk.Scale(
            parent,
            from_=from_,
            to=to,
            orient="horizontal",
            variable=variable,
            length=220,
            showvalue=False,
            command=on_change,
        ).grid(row=row, column=1, padx=4)
        tk.Label(parent, textvariable=val_str, width=5, anchor="w").grid(
            row=row, column=2
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _open_setup(self):
        if self._running:
            messagebox.showwarning(
                "Monitoring active",
                "Stop monitoring before editing ROIs.",
                parent=self.root,
            )
            return
        SetupWindow(self.root)

    def _toggle_debug(self):
        self._debug_on = not self._debug_on
        if self._debug_on:
            self._debug_btn.config(bg="#1565C0", fg="white", relief="sunken")
            self._open_debug_overlay()
        else:
            self._debug_btn.config(bg=self.root.cget("bg"), fg="black", relief="raised")
            if self._debug_overlay:
                self._debug_overlay.hide()
                self._debug_overlay = None

    def _open_debug_overlay(self):
        if self._debug_overlay:
            return
        cfg = config.load()
        with mss.mss() as sct:
            mon = sct.monitors[cfg.get("monitor_index", 1)]
        self._debug_overlay = DebugOverlay(self.root)
        self._debug_overlay.show(mon["left"], mon["top"], mon["width"], mon["height"])
        if not self._running:
            # Static view: show ROI positions before monitoring starts
            rois = cfg.get("rois", [])
            self._debug_overlay.update([
                {"id": r["id"], "x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"],
                 "current": 0, "peak": 0,
                 "threshold": r.get("threshold", 30), "active": False}
                for r in rois
            ])

    def _toggle_start_stop(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _save_display_settings(self):
        cfg = config.load()
        cfg["display_x"]     = self._disp_x.get() / 100
        cfg["display_y"]     = self._disp_y.get() / 100
        cfg["font_size"]     = self._font_size.get()
        cfg["sub_font_size"] = self._sub_font.get()
        cfg["sub_gap"]       = self._sub_gap.get()
        config.save(cfg)
        if self._overlay:
            self._overlay.set_position(cfg["display_x"], cfg["display_y"])
            self._overlay.set_font_size(cfg["font_size"])
            self._overlay.set_sub_font_size(cfg["sub_font_size"])
            self._overlay.set_sub_gap(cfg["sub_gap"])

    def _start(self):
        try:
            self._do_start()
        except Exception as e:
            logger.exception("Error during start")
            messagebox.showerror("Start failed", str(e), parent=self.root)

    def _do_start(self):
        self._save_display_settings()
        cfg = config.load()
        rois = cfg.get("rois", [])

        if not rois:
            messagebox.showerror("No ROIs", "No ROIs defined — run Setup first.", parent=self.root)
            return

        missing = list(dict.fromkeys(r["id"] for r in rois if r.get("baseline") is None))
        if missing:
            messagebox.showerror(
                "Missing Baselines",
                f"ROIs without a baseline: {', '.join(missing)}\n\n"
                "Open Setup → Sample Baselines → Save.",
                parent=self.root,
            )
            return

        self._overlay = Overlay(
            self.root,
            display_interval_ms=cfg.get("display_interval_ms", 1000),
            relx=cfg.get("display_x", 0.5),
            rely=cfg.get("display_y", 0.5),
            font_size=cfg.get("font_size", 180),
            sub_font_size=cfg.get("sub_font_size", 22),
            sub_gap=cfg.get("sub_gap", 0),
        )
        if self._debug_on:
            self._open_debug_overlay()  # reuse if already open

        self._monitor = ScreenMonitor(
            rois=rois,
            monitor_index=cfg.get("monitor_index", 1),
            interval_ms=cfg.get("check_interval_ms", 1000),
            on_update=self._on_monitor_update,
        )
        self._monitor.start()
        self._running = True
        self._start_stop_btn.config(text="■  Stop", bg="#c62828")
        logger.info("Monitoring started — %d ROIs", len(rois))

    def _stop(self):
        if self._monitor:
            self._monitor.stop()
            self._monitor = None
        if self._overlay:
            self._overlay.hide()
            self._overlay = None
        self._running = False
        self._start_stop_btn.config(text="▶  Start", bg="#2e7d32")
        self._active_var.set("—")
        if self._debug_overlay:
            if self._debug_on:
                # Revert to static view after stopping
                cfg = config.load()
                rois = cfg.get("rois", [])
                self._debug_overlay.update([
                    {"id": r["id"], "x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"],
                     "current": 0, "peak": 0,
                     "threshold": r.get("threshold", 30), "active": False}
                    for r in rois
                ])
            else:
                self._debug_overlay.hide()
                self._debug_overlay = None

    def _on_monitor_update(self, active, roi_data):
        def _apply():
            self._active_var.set(", ".join(active) if active else "—")
            if self._overlay:
                self._overlay.update(active)
            if self._debug_overlay:
                self._debug_overlay.update(roi_data)
        self.root.after(0, _apply)

    # ------------------------------------------------------------------
    # Window management
    # ------------------------------------------------------------------

    def _on_configure(self, event):
        if event.widget is not self.root:
            return
        if self._save_pos_job:
            self.root.after_cancel(self._save_pos_job)
        self._save_pos_job = self.root.after(500, self._save_position)

    def _save_position(self):
        self._save_pos_job = None
        cfg = config.load()
        cfg["window_x"] = self.root.winfo_x()
        cfg["window_y"] = self.root.winfo_y()
        config.save(cfg)

    def _toggle_window(self):
        self.root.after(0, self._do_toggle)

    def _do_toggle(self):
        if self._visible:
            self.root.withdraw()
            self._visible = False
        else:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self._visible = True

    def _on_close(self):
        logger.info("App closed")
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        self._stop()
        self.root.destroy()


if __name__ == "__main__":
    App()
