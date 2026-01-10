"""Custom exceptions for YouTube Playlist Creator."""
from typing import Optional


class PlaylistCreatorError(Exception):
    """Base exception for all playlist creator errors."""
    pass


class ParseError(PlaylistCreatorError):
    """Error parsing Markdown file."""

    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None):
        self.line = line
        self.column = column
        location = ""
        if line is not None:
            location = f" (line {line}"
            if column is not None:
                location += f", column {column}"
            location += ")"
        super().__init__(f"{message}{location}")


class AuthenticationError(PlaylistCreatorError):
    """Error during OAuth authentication."""
    pass


class QuotaExceededError(PlaylistCreatorError):
    """YouTube API daily quota exceeded."""

    def __init__(self, message: str = "Daily quota exceeded (10,000 units). Resets at midnight Pacific Time."):
        super().__init__(message)


class VideoUnavailableError(PlaylistCreatorError):
    """Video not found or blocked."""

    def __init__(self, video_id: str, track_name: Optional[str] = None):
        self.video_id = video_id
        self.track_name = track_name
        msg = f"Video unavailable: {video_id}"
        if track_name:
            msg += f" ({track_name})"
        super().__init__(msg)


class PlaylistNotFoundError(PlaylistCreatorError):
    """YouTube playlist not found or inaccessible."""

    def __init__(self, playlist_id: str):
        self.playlist_id = playlist_id
        super().__init__(f"Playlist not found or inaccessible: {playlist_id}")


class YouTubeAPIError(PlaylistCreatorError):
    """Generic YouTube API error."""
    pass


class CacheError(PlaylistCreatorError):
    """Error reading or writing cache."""
    pass
