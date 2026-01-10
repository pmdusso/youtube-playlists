"""Utility functions for YouTube Playlist Creator."""
import re
import time
import logging
from dataclasses import dataclass
from functools import wraps
from typing import Callable, TypeVar

from playlist_creator.core.exceptions import YouTubeAPIError


logger = logging.getLogger("playlist_creator")

T = TypeVar("T")


@dataclass(frozen=True)
class Icons:
    """Unicode icons for consistent output formatting."""
    FOLDER = "📂"
    PLAYLIST = "📋"
    SEARCH = "🔍"
    SUCCESS = "✓"
    WARNING = "⚠"
    ERROR = "❌"
    SKIP = "⏭"
    CACHED = "💾"
    LOCK = "🔐"


def build_search_query(title: str, artist: str) -> str:
    """Build a YouTube search query for a song."""
    return f'"{title}" "{artist}" official music video'


def format_duration(duration: str) -> str:
    """Convert ISO 8601 duration to human-readable format."""
    if re.match(r"^\d+:\d{2}(:\d{2})?$", duration):
        return duration
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return duration
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (YouTubeAPIError,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
            raise RuntimeError("Unreachable")
        return wrapper
    return decorator


def format_track_status(index: int, total: int, title: str, artist: str, status_icon: str, detail: str = "") -> str:
    """Format a track status line for output."""
    prefix = f"[{index}/{total}]"
    track_name = f"{title} - {artist}"
    lines = [f"{prefix} {track_name}"]
    if detail:
        lines.append(f"       {status_icon} {detail}")
    else:
        lines.append(f"       {status_icon}")
    return "\n".join(lines)
