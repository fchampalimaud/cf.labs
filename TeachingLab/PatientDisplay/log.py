import logging
import os
import sys
from logging.handlers import RotatingFileHandler

if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

LOG_FILE = os.path.join(_BASE, "PatientDisplay.log")

_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=1 * 1024 * 1024,  # 1 MB then rotate
    backupCount=2,
    encoding="utf-8",
)
_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(_handler)


def get(name="PatientDisplay"):
    return logging.getLogger(name)
