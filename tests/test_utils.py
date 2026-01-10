"""Tests for utility functions."""
import pytest
import time
from unittest.mock import Mock, patch
from playlist_creator.core.utils import (
    build_search_query,
    format_duration,
    retry_with_backoff,
    Icons,
)
from playlist_creator.core.exceptions import YouTubeAPIError


class TestBuildSearchQuery:
    def test_simple_query(self):
        query = build_search_query("Yeah!", "Usher")
        assert '"Yeah!"' in query
        assert '"Usher"' in query
        assert "official" in query.lower()

    def test_query_with_featuring(self):
        query = build_search_query("Yeah!", "Usher ft. Lil Jon & Ludacris")
        assert '"Yeah!"' in query
        assert '"Usher ft. Lil Jon & Ludacris"' in query


class TestFormatDuration:
    def test_format_iso_duration(self):
        assert format_duration("PT3M45S") == "3:45"
        assert format_duration("PT4M11S") == "4:11"
        assert format_duration("PT1H2M30S") == "1:02:30"

    def test_format_seconds_only(self):
        assert format_duration("PT45S") == "0:45"

    def test_format_already_formatted(self):
        assert format_duration("3:45") == "3:45"


class TestRetryWithBackoff:
    def test_success_no_retry(self):
        mock_func = Mock(return_value="success")
        decorated = retry_with_backoff(max_retries=3)(mock_func)
        result = decorated()
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_then_success(self):
        mock_func = Mock(side_effect=[YouTubeAPIError("fail"), "success"])
        decorated = retry_with_backoff(max_retries=3, base_delay=0.01)(mock_func)
        result = decorated()
        assert result == "success"
        assert mock_func.call_count == 2

    def test_max_retries_exceeded(self):
        mock_func = Mock(side_effect=YouTubeAPIError("always fails"))
        decorated = retry_with_backoff(max_retries=3, base_delay=0.01)(mock_func)
        with pytest.raises(YouTubeAPIError):
            decorated()
        assert mock_func.call_count == 3


class TestIcons:
    def test_icons_exist(self):
        assert Icons.SUCCESS == "✓"
        assert Icons.WARNING == "⚠"
        assert Icons.ERROR == "❌"
        assert Icons.SEARCH == "🔍"
