import tkinter as tk
import uuid
from tkinter import messagebox, simpledialog

import mss
import numpy as np
from PIL import Image, ImageTk

import config


class SetupWindow:
    """
    Modal window for drawing, labelling, and saving ROIs.

    Workflow:
      1. A screenshot of the monitored monitor is displayed on a canvas.
      2. User click-drags to draw rectangles (ROIs).
      3. A label dialog asks for the cabinet name/number.
      4. Right-click an existing ROI to delete it.
      5. "Sample Baselines" captures current screen brightness for every ROI.
      6. "Save & Close" writes config.json.
    """

    def __init__(self, parent):
        self.parent = parent
        self.cfg = config.load()
        self.rois: list[dict] = list(self.cfg.get("rois", []))
        for roi in self.rois:
            roi.setdefault("key", uuid.uuid4().hex)
        self.scale = 1.0
        self.photo = None  # keep reference so GC doesn't collect it

        self.win = tk.Toplevel(parent)
        self.win.title("ROI Setup")
        self.win.grab_set()  # modal

        self._build_toolbar()
        self._build_canvas()
        self._build_statusbar()

        self._take_screenshot()
        self._redraw_all()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        bar = tk.Frame(self.win)
        bar.pack(fill="x", padx=6, pady=4)

        tk.Button(bar, text="Refresh Screenshot", command=self._take_screenshot).pack(
            side="left", padx=2
        )
        tk.Button(
            bar,
            text="Sample Baselines",
            command=self._sample_baselines,
            bg="#1565C0",
            fg="white",
        ).pack(side="left", padx=2)

        tk.Label(bar, text="  Threshold:").pack(side="left")
        self._threshold_var = tk.IntVar(value=self.cfg.get("threshold", 30))
        tk.Spinbox(bar, from_=1, to=200, textvariable=self._threshold_var, width=5).pack(
            side="left"
        )

        tk.Button(
            bar, text="Save & Close", command=self._save, bg="#2e7d32", fg="white"
        ).pack(side="right", padx=2)

    def _build_canvas(self):
        frame = tk.Frame(self.win)
        frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(frame, cursor="crosshair", bg="#333")
        vsb = tk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        hsb = tk.Scrollbar(self.win, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        hsb.pack(fill="x", side="bottom")
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<ButtonPress-3>", self._on_right_click)

        self._start_x = self._start_y = None
        self._rubber = None

    def _build_statusbar(self):
        self._status = tk.StringVar(
            value="Click-drag to draw an ROI  |  Right-click to delete"
        )
        tk.Label(
            self.win, textvariable=self._status, anchor="w", relief="sunken", padx=4
        ).pack(fill="x", side="bottom")

    # ------------------------------------------------------------------
    # Screenshot
    # ------------------------------------------------------------------

    def _take_screenshot(self):
        # Hide the setup window so it doesn't appear in the capture
        self.win.withdraw()
        self._status_pending = "Screenshot refreshed."
        self.win.after(300, self._do_take_screenshot)

    def _do_take_screenshot(self):
        mon_idx = self.cfg.get("monitor_index", 1)
        with mss.mss() as sct:
            mon = sct.monitors[mon_idx]
            shot = sct.grab(mon)
            self._screen_w = mon["width"]
            self._screen_h = mon["height"]
            self._shot_arr = np.array(shot)  # BGRA, kept for baseline sampling
            pil = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

        self.win.deiconify()

        max_w, max_h = 1280, 720
        self.scale = min(max_w / self._screen_w, max_h / self._screen_h, 1.0)
        dw = int(self._screen_w * self.scale)
        dh = int(self._screen_h * self.scale)

        pil = pil.resize((dw, dh), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(pil)

        self.canvas.config(width=dw, height=dh, scrollregion=(0, 0, dw, dh))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo, tags="bg")

        self.win.geometry(f"{min(dw + 20, 1300)}x{min(dh + 90, 820)}")
        self._redraw_all()
        self._status.set(getattr(self, "_status_pending", "Screenshot refreshed."))

    # ------------------------------------------------------------------
    # ROI drawing helpers
    # ------------------------------------------------------------------

    def _s2c(self, sx, sy):
        return int(sx * self.scale), int(sy * self.scale)

    def _c2s(self, cx, cy):
        return int(cx / self.scale), int(cy / self.scale)

    def _redraw_all(self):
        self.canvas.delete("roi")
        for roi in self.rois:
            self._draw_roi(roi)

    def _draw_roi(self, roi):
        x1, y1 = self._s2c(roi["x"], roi["y"])
        x2, y2 = self._s2c(roi["x"] + roi["w"], roi["y"] + roi["h"])
        tag = f"roi_{roi['key']}"
        self.canvas.delete(tag)

        self.canvas.create_rectangle(
            x1, y1, x2, y2, outline="red", width=2, tags=("roi", tag)
        )
        self.canvas.create_text(
            x1 + 4, y1 + 4,
            anchor="nw", text=roi["id"],
            fill="yellow", font=("Arial", 11, "bold"),
            tags=("roi", tag),
        )
        if roi.get("baseline") is not None:
            self.canvas.create_text(
                x1 + 4, y2 - 4,
                anchor="sw", text=f"bl={roi['baseline']:.0f}",
                fill="cyan", font=("Arial", 9),
                tags=("roi", tag),
            )

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------

    def _next_label(self):
        nums = [int(r["id"]) for r in self.rois if r["id"].isdigit()]
        return str(max(nums) + 1) if nums else "1"

    def _on_press(self, event):
        self._start_x = self.canvas.canvasx(event.x)
        self._start_y = self.canvas.canvasy(event.y)
        self._rubber = None

    def _on_drag(self, event):
        if self._start_x is None:
            return
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self._rubber:
            self.canvas.delete(self._rubber)
        self._rubber = self.canvas.create_rectangle(
            self._start_x, self._start_y, cx, cy,
            outline="yellow", width=2, dash=(6, 4),
        )

    def _on_release(self, event):
        if self._start_x is None or self._rubber is None:
            return
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.delete(self._rubber)
        self._rubber = None

        x1 = min(self._start_x, cx)
        y1 = min(self._start_y, cy)
        x2 = max(self._start_x, cx)
        y2 = max(self._start_y, cy)
        self._start_x = None

        if (x2 - x1) < 5 or (y2 - y1) < 5:
            return

        label = simpledialog.askstring(
            "Cabinet Label", "Enter cabinet name / number:",
            parent=self.win,
            initialvalue=self._next_label(),
        )
        if not label or not label.strip():
            return
        label = label.strip()

        sx1, sy1 = self._c2s(x1, y1)
        sx2, sy2 = self._c2s(x2, y2)

        roi = {
            "id": label,
            "key": uuid.uuid4().hex,
            "x": sx1,
            "y": sy1,
            "w": max(sx2 - sx1, 1),
            "h": max(sy2 - sy1, 1),
            "baseline": None,
            "threshold": self._threshold_var.get(),
        }
        self.rois.append(roi)
        self._draw_roi(roi)
        self._status.set(f"ROI '{label}' added. Click 'Sample Baselines' when ready.")

    def _on_right_click(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        hits = self.canvas.find_overlapping(cx - 3, cy - 3, cx + 3, cy + 3)
        for item in hits:
            for tag in self.canvas.gettags(item):
                if tag.startswith("roi_"):
                    roi_key = tag[4:]
                    roi = next((r for r in self.rois if r["key"] == roi_key), None)
                    if roi is None:
                        return
                    if messagebox.askyesno("Delete ROI", f"Delete '{roi['id']}'?", parent=self.win):
                        self.rois = [r for r in self.rois if r["key"] != roi_key]
                        self.canvas.delete(tag)
                        self._status.set(f"ROI '{roi['id']}' deleted.")
                    return

    # ------------------------------------------------------------------
    # Baseline sampling
    # ------------------------------------------------------------------

    def _sample_baselines(self):
        gray = self._shot_arr[:, :, :3].max(axis=2)
        for roi in self.rois:
            patch = gray[roi["y"] : roi["y"] + roi["h"], roi["x"] : roi["x"] + roi["w"]]
            roi["baseline"] = float(patch.mean()) if patch.size > 0 else 0.0

        self._redraw_all()
        self._status.set(
            f"Baselines sampled for {len(self.rois)} ROIs. Save when ready."
        )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _save(self):
        unsampled = [r["id"] for r in self.rois if r.get("baseline") is None]
        if unsampled:
            if not messagebox.askyesno(
                "Missing Baselines",
                f"These ROIs have no baseline yet: {', '.join(unsampled)}\n\nSave anyway?",
                parent=self.win,
            ):
                return

        threshold = self._threshold_var.get()
        for roi in self.rois:
            roi["threshold"] = threshold

        self.cfg["rois"] = self.rois
        self.cfg["threshold"] = threshold
        config.save(self.cfg)
        messagebox.showinfo(
            "Saved", f"{len(self.rois)} ROIs saved to config.json.", parent=self.win
        )
        self.win.destroy()
