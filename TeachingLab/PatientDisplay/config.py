import json
import os
import sys

if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(_BASE, "config.json")

DEFAULT = {
    "rois": [],
    "check_interval_ms": 1000,
    "display_interval_ms": 1000,
    "threshold": 30,
    "monitor_index": 1,
    "display_x": 0.5,
    "display_y": 0.5,
    "font_size": 180,
    "sub_font_size": 22,
    "sub_gap": 0,
    "window_x": 100,
    "window_y": 100,
}


def load():
    if not os.path.exists(CONFIG_FILE):
        return dict(DEFAULT)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
