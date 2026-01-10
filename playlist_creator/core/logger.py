"""Logging configuration for YouTube Playlist Creator."""
import logging
import sys
from datetime import datetime
from pathlib import Path

from config import LOGS_DIR


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for console and file output."""
    logger = logging.getLogger("playlist_creator")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)

    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / f"{datetime.now():%Y-%m-%d}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
        logger.addHandler(file_handler)
    except OSError:
        pass

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    return logger
