import logging
import threading
import numpy as np
import mss

logger = logging.getLogger("PatientDisplay")


class ScreenMonitor:
    def __init__(self, rois, monitor_index=1, interval_ms=1000, on_update=None):
        self.rois = rois
        self.monitor_index = monitor_index
        self.interval = interval_ms / 1000.0
        self.on_update = on_update
        self._stop_event = threading.Event()
        self._thread = None
        self._log_counter = 0
        self._peaks = {}  # roi_id -> highest current value seen

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        with mss.mss() as sct:
            monitor = sct.monitors[self.monitor_index]
            while not self._stop_event.wait(self.interval):
                frame = np.array(sct.grab(monitor))
                # Use max(R,G,B) per pixel — detects any color change,
                # not just brightness shifts (e.g. yellow on black background).
                gray = frame[:, :, :3].max(axis=2)

                active = []
                roi_data = []
                self._log_counter += 1
                do_log = (self._log_counter % 10) == 1  # log every ~10 s
                for roi in self.rois:
                    x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]
                    patch = gray[y : y + h, x : x + w]
                    if patch.size == 0:
                        continue
                    threshold = roi.get("threshold", 30)
                    current = float(patch.mean())
                    peak = max(self._peaks.get(roi["id"], 0.0), current)
                    self._peaks[roi["id"]] = peak
                    is_active = current > threshold
                    if do_log:
                        logger.info(
                            "ROI '%s': current=%.1f  peak=%.1f  threshold=%s  active=%s",
                            roi["id"], current, peak, threshold, is_active,
                        )
                    if is_active:
                        active.append(roi["id"])
                    roi_data.append({
                        "id": roi["id"],
                        "x": x, "y": y, "w": w, "h": h,
                        "current": current,
                        "peak": peak,
                        "threshold": threshold,
                        "active": is_active,
                    })

                if self.on_update:
                    self.on_update(active, roi_data)
