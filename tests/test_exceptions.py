"""Tests for custom exceptions."""
import pytest
from playlist_creator.core.exceptions import (
    PlaylistCreatorError,
    ParseError,
    AuthenticationError,
    QuotaExceededError,
    VideoUnavailableError,
    PlaylistNotFoundError,
    YouTubeAPIError,
    CacheError,
)


class TestExceptions:
    def test_base_exception(self):
        with pytest.raises(PlaylistCreatorError):
            raise PlaylistCreatorError("base error")

    def test_parse_error_with_location(self):
        error = ParseError("Invalid table", line=15, column=3)
        assert error.line == 15
        assert error.column == 3
        assert "line 15" in str(error)

    def test_quota_exceeded_error(self):
        error = QuotaExceededError()
        assert "quota" in str(error).lower()

    def test_video_unavailable_with_id(self):
        error = VideoUnavailableError("abc123", "Yeah! - Usher")
        assert error.video_id == "abc123"
        assert "abc123" in str(error)
