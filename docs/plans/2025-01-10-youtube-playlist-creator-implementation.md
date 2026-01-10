# YouTube Playlist Creator - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that creates and syncs YouTube playlists from Markdown files.

**Architecture:** Three commands (`search`, `create`, `sync`) share core modules for parsing, caching, and YouTube API interaction. OAuth handles authentication. Global cache stores search results.

**Tech Stack:** Python 3.11+, click (CLI), google-api-python-client (YouTube API), google-auth-oauthlib (OAuth), pytest (testing)

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `playlist_creator/__init__.py`

**Step 1: Create requirements.txt**

```
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.1.0
click>=8.1.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

**Step 2: Create config.py**

```python
"""Configuration constants for YouTube Playlist Creator."""
from pathlib import Path

# Cache location
CACHE_DIR = Path.home() / ".youtube-playlist-cache"
SEARCHES_FILE = CACHE_DIR / "searches.json"
CREDENTIALS_DIR = CACHE_DIR / "credentials"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
LOGS_DIR = CACHE_DIR / "logs"
IN_PROGRESS_DIR = CACHE_DIR / ".in_progress"

# YouTube API
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
MUSIC_CATEGORY_ID = "10"

# Rate limiting
RATE_LIMIT_DELAY = 0.5  # seconds between API requests
MAX_SEARCH_RESULTS = 3  # top N matches to cache

# Retry settings
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0  # seconds

# Default playlist privacy
DEFAULT_PRIVACY = "private"
```

**Step 3: Create package init**

```python
"""YouTube Playlist Creator - Create playlists from Markdown files."""
__version__ = "1.0.0"
```

**Step 4: Create virtual environment and install dependencies**

Run:
```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

**Step 5: Commit**

```bash
git add requirements.txt config.py playlist_creator/
git commit -m "chore: project setup with dependencies and config"
```

---

## Task 2: Data Models

**Files:**
- Create: `playlist_creator/models/__init__.py`
- Create: `playlist_creator/models/track.py`
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`

**Step 1: Write failing test for Track model**

```python
# tests/test_models.py
"""Tests for data models."""
import pytest
from playlist_creator.models.track import Track, SearchMatch, CacheEntry, CacheStatus
from datetime import datetime


class TestTrack:
    def test_track_creation(self):
        track = Track(position=1, title="Yeah!", artist="Usher")
        assert track.position == 1
        assert track.title == "Yeah!"
        assert track.artist == "Usher"

    def test_track_query_property(self):
        track = Track(position=1, title="Yeah!", artist="Usher ft. Lil Jon")
        assert track.query == "Yeah! - Usher ft. Lil Jon"


class TestSearchMatch:
    def test_search_match_creation(self):
        match = SearchMatch(
            video_id="abc123",
            title="Yeah! (Official Video)",
            channel="UsherVEVO",
            duration="4:11"
        )
        assert match.video_id == "abc123"
        assert match.duration == "4:11"


class TestCacheEntry:
    def test_cache_entry_found(self):
        match = SearchMatch("abc123", "Title", "Channel", "3:45")
        entry = CacheEntry(
            query="Song - Artist",
            status=CacheStatus.FOUND,
            matches=[match],
            selected=0,
            searched_at=datetime(2025, 1, 10, 20, 30),
            query_used='"Song" "Artist" official'
        )
        assert entry.status == CacheStatus.FOUND
        assert len(entry.matches) == 1
        assert entry.selected == 0

    def test_cache_entry_not_found(self):
        entry = CacheEntry(
            query="Unknown - Artist",
            status=CacheStatus.NOT_FOUND,
            matches=[],
            selected=None,
            searched_at=datetime(2025, 1, 10, 20, 30),
            query_used='"Unknown" "Artist" official'
        )
        assert entry.status == CacheStatus.NOT_FOUND
        assert entry.matches == []
        assert entry.selected is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create models package init**

```python
# playlist_creator/models/__init__.py
"""Data models for YouTube Playlist Creator."""
from .track import Track, SearchMatch, CacheEntry, CacheStatus

__all__ = ["Track", "SearchMatch", "CacheEntry", "CacheStatus"]
```

**Step 4: Implement models**

```python
# playlist_creator/models/track.py
"""Data models for tracks and cache entries."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class CacheStatus(Enum):
    """Status of a cache entry."""
    FOUND = "found"
    NOT_FOUND = "not_found"


@dataclass
class Track:
    """A song from the Markdown file."""
    position: int
    title: str
    artist: str

    @property
    def query(self) -> str:
        """Normalized query string for searching and cache lookup."""
        return f"{self.title} - {self.artist}"


@dataclass
class SearchMatch:
    """A YouTube search result."""
    video_id: str
    title: str
    channel: str
    duration: str


@dataclass
class CacheEntry:
    """A cached search result."""
    query: str
    status: CacheStatus
    matches: list[SearchMatch]
    selected: Optional[int]
    searched_at: datetime
    query_used: str
```

**Step 5: Create tests package init**

```python
# tests/__init__.py
"""Tests for YouTube Playlist Creator."""
```

**Step 6: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: All 4 tests PASS

**Step 7: Commit**

```bash
git add playlist_creator/models/ tests/
git commit -m "feat: add data models (Track, SearchMatch, CacheEntry)"
```

---

## Task 3: Exceptions

**Files:**
- Create: `playlist_creator/core/__init__.py`
- Create: `playlist_creator/core/exceptions.py`
- Create: `tests/test_exceptions.py`

**Step 1: Write failing test**

```python
# tests/test_exceptions.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_exceptions.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create core package init**

```python
# playlist_creator/core/__init__.py
"""Core modules for YouTube Playlist Creator."""
```

**Step 4: Implement exceptions**

```python
# playlist_creator/core/exceptions.py
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
```

**Step 5: Run tests**

Run: `pytest tests/test_exceptions.py -v`
Expected: All 4 tests PASS

**Step 6: Commit**

```bash
git add playlist_creator/core/ tests/test_exceptions.py
git commit -m "feat: add custom exception classes"
```

---

## Task 4: Markdown Parser

**Files:**
- Create: `playlist_creator/core/parser.py`
- Create: `tests/test_parser.py`
- Create: `tests/fixtures/valid_playlist.md`
- Create: `tests/fixtures/invalid_playlist.md`

**Step 1: Create test fixtures**

```markdown
# tests/fixtures/valid_playlist.md
# 2000s R&B & Hip-Hop Classics

This is a test playlist with some classic tracks.

| # | Música | Artista |
|---|--------|---------|
| 1 | Yeah! | Usher ft. Lil Jon & Ludacris |
| 2 | In Da Club | 50 Cent |
| 3 | Crazy in Love | Beyoncé ft. Jay-Z |
```

```markdown
# tests/fixtures/invalid_playlist.md
# Invalid Playlist

| # | Song | Singer |
|---|------|--------|
| 1 | Test | Artist |
```

**Step 2: Write failing tests**

```python
# tests/test_parser.py
"""Tests for Markdown parser."""
import pytest
from pathlib import Path
from playlist_creator.core.parser import parse_markdown, parse_markdown_string
from playlist_creator.core.exceptions import ParseError
from playlist_creator.models import Track


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestParseMarkdown:
    def test_parse_valid_playlist(self):
        result = parse_markdown(FIXTURES_DIR / "valid_playlist.md")

        assert result.name == "2000s R&B & Hip-Hop Classics"
        assert len(result.tracks) == 3

        assert result.tracks[0] == Track(1, "Yeah!", "Usher ft. Lil Jon & Ludacris")
        assert result.tracks[1] == Track(2, "In Da Club", "50 Cent")
        assert result.tracks[2] == Track(3, "Crazy in Love", "Beyoncé ft. Jay-Z")

    def test_parse_invalid_columns(self):
        with pytest.raises(ParseError) as exc_info:
            parse_markdown(FIXTURES_DIR / "invalid_playlist.md")
        assert "Música" in str(exc_info.value) or "Artista" in str(exc_info.value)

    def test_parse_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_markdown(Path("/nonexistent/file.md"))


class TestParseMarkdownString:
    def test_parse_simple_string(self):
        content = """# Test Playlist

| # | Música | Artista |
|---|--------|---------|
| 1 | Bohemian Rhapsody | Queen |
"""
        result = parse_markdown_string(content)
        assert result.name == "Test Playlist"
        assert len(result.tracks) == 1
        assert result.tracks[0].title == "Bohemian Rhapsody"

    def test_parse_multiple_tables(self):
        content = """# Multi-Table Playlist

First section:

| # | Música | Artista |
|---|--------|---------|
| 1 | Song A | Artist A |
| 2 | Song B | Artist B |

Second section:

| # | Música | Artista |
|---|--------|---------|
| 3 | Song C | Artist C |
"""
        result = parse_markdown_string(content)
        assert len(result.tracks) == 3
        assert result.tracks[2].position == 3

    def test_parse_no_title(self):
        content = """| # | Música | Artista |
|---|--------|---------|
| 1 | Song | Artist |
"""
        with pytest.raises(ParseError) as exc_info:
            parse_markdown_string(content)
        assert "title" in str(exc_info.value).lower() or "H1" in str(exc_info.value)

    def test_strips_whitespace(self):
        content = """# Test

| # | Música | Artista |
|---|--------|---------|
| 1 |   Spaced Song   |   Spaced Artist   |
"""
        result = parse_markdown_string(content)
        assert result.tracks[0].title == "Spaced Song"
        assert result.tracks[0].artist == "Spaced Artist"
```

**Step 3: Run tests to verify they fail**

Run: `pytest tests/test_parser.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 4: Implement parser**

```python
# playlist_creator/core/parser.py
"""Markdown parser for playlist files."""
import re
from dataclasses import dataclass
from pathlib import Path

from playlist_creator.core.exceptions import ParseError
from playlist_creator.models import Track


@dataclass
class ParsedPlaylist:
    """Result of parsing a Markdown playlist file."""
    name: str
    tracks: list[Track]


def parse_markdown(file_path: Path) -> ParsedPlaylist:
    """Parse a Markdown file into a playlist.

    Args:
        file_path: Path to the Markdown file.

    Returns:
        ParsedPlaylist with name and tracks.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ParseError: If file format is invalid.
    """
    content = file_path.read_text(encoding="utf-8")
    return parse_markdown_string(content)


def parse_markdown_string(content: str) -> ParsedPlaylist:
    """Parse Markdown content string into a playlist.

    Args:
        content: Markdown content as string.

    Returns:
        ParsedPlaylist with name and tracks.

    Raises:
        ParseError: If content format is invalid.
    """
    # Extract H1 title
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if not title_match:
        raise ParseError("No H1 title found. File must start with '# Playlist Name'")

    name = title_match.group(1).strip()

    # Find all tables
    tracks = []
    table_pattern = re.compile(
        r"\|[^|]*#[^|]*\|[^|]*Música[^|]*\|[^|]*Artista[^|]*\|.*?\n"  # Header
        r"\|[-:\s|]+\|.*?\n"  # Separator
        r"((?:\|.*?\n)+)",  # Rows
        re.IGNORECASE
    )

    tables = table_pattern.findall(content)

    if not tables:
        raise ParseError(
            "No valid table found. Table must have columns: '#', 'Música', 'Artista'"
        )

    for table_rows in tables:
        for row in table_rows.strip().split("\n"):
            if not row.strip():
                continue

            cells = [cell.strip() for cell in row.split("|")]
            # Remove empty cells from split
            cells = [c for c in cells if c]

            if len(cells) >= 3:
                try:
                    position = int(cells[0])
                    title = cells[1].strip()
                    artist = cells[2].strip()
                    tracks.append(Track(position=position, title=title, artist=artist))
                except (ValueError, IndexError):
                    continue  # Skip malformed rows

    if not tracks:
        raise ParseError("No valid tracks found in table")

    # Sort by position
    tracks.sort(key=lambda t: t.position)

    return ParsedPlaylist(name=name, tracks=tracks)
```

**Step 5: Create fixtures directory and files**

Run: `mkdir -p tests/fixtures`

**Step 6: Run tests**

Run: `pytest tests/test_parser.py -v`
Expected: All 7 tests PASS

**Step 7: Commit**

```bash
git add playlist_creator/core/parser.py tests/test_parser.py tests/fixtures/
git commit -m "feat: add Markdown parser for playlist files"
```

---

## Task 5: Cache Manager

**Files:**
- Create: `playlist_creator/core/cache.py`
- Create: `tests/test_cache.py`

**Step 1: Write failing tests**

```python
# tests/test_cache.py
"""Tests for cache manager."""
import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from playlist_creator.core.cache import CacheManager
from playlist_creator.models import CacheEntry, CacheStatus, SearchMatch


class TestCacheManager:
    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create a temporary cache directory."""
        cache_dir = tmp_path / ".youtube-playlist-cache"
        return cache_dir

    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create a cache manager with temp directory."""
        with patch("playlist_creator.core.cache.CACHE_DIR", temp_cache_dir):
            with patch("playlist_creator.core.cache.SEARCHES_FILE", temp_cache_dir / "searches.json"):
                return CacheManager()

    def test_init_creates_directories(self, cache_manager, temp_cache_dir):
        cache_manager.ensure_initialized()
        assert temp_cache_dir.exists()

    def test_get_nonexistent_entry(self, cache_manager):
        cache_manager.ensure_initialized()
        result = cache_manager.get("Unknown - Artist")
        assert result is None

    def test_save_and_get_entry(self, cache_manager):
        cache_manager.ensure_initialized()

        match = SearchMatch(
            video_id="abc123",
            title="Test Video",
            channel="TestChannel",
            duration="3:45"
        )
        entry = CacheEntry(
            query="Test - Artist",
            status=CacheStatus.FOUND,
            matches=[match],
            selected=0,
            searched_at=datetime(2025, 1, 10, 20, 30),
            query_used='"Test" "Artist" official'
        )

        cache_manager.save(entry)

        result = cache_manager.get("Test - Artist")
        assert result is not None
        assert result.status == CacheStatus.FOUND
        assert result.matches[0].video_id == "abc123"

    def test_persistence(self, cache_manager, temp_cache_dir):
        cache_manager.ensure_initialized()

        match = SearchMatch("xyz789", "Persisted", "Channel", "2:30")
        entry = CacheEntry(
            query="Persist - Test",
            status=CacheStatus.FOUND,
            matches=[match],
            selected=0,
            searched_at=datetime.now(),
            query_used='"Persist" "Test"'
        )
        cache_manager.save(entry)

        # Create new manager instance
        with patch("playlist_creator.core.cache.CACHE_DIR", temp_cache_dir):
            with patch("playlist_creator.core.cache.SEARCHES_FILE", temp_cache_dir / "searches.json"):
                new_manager = CacheManager()
                result = new_manager.get("Persist - Test")

        assert result is not None
        assert result.matches[0].video_id == "xyz789"

    def test_get_selected_video_id(self, cache_manager):
        cache_manager.ensure_initialized()

        matches = [
            SearchMatch("first", "First", "Ch1", "3:00"),
            SearchMatch("second", "Second", "Ch2", "3:01"),
            SearchMatch("third", "Third", "Ch3", "3:02"),
        ]
        entry = CacheEntry(
            query="Multi - Match",
            status=CacheStatus.FOUND,
            matches=matches,
            selected=1,  # Select second
            searched_at=datetime.now(),
            query_used='"Multi" "Match"'
        )
        cache_manager.save(entry)

        video_id = cache_manager.get_selected_video_id("Multi - Match")
        assert video_id == "second"

    def test_get_selected_video_id_not_found(self, cache_manager):
        cache_manager.ensure_initialized()

        entry = CacheEntry(
            query="Missing - Song",
            status=CacheStatus.NOT_FOUND,
            matches=[],
            selected=None,
            searched_at=datetime.now(),
            query_used='"Missing" "Song"'
        )
        cache_manager.save(entry)

        video_id = cache_manager.get_selected_video_id("Missing - Song")
        assert video_id is None
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cache.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement cache manager**

```python
# playlist_creator/core/cache.py
"""Cache manager for YouTube search results."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import CACHE_DIR, SEARCHES_FILE
from playlist_creator.core.exceptions import CacheError
from playlist_creator.models import CacheEntry, CacheStatus, SearchMatch


class CacheManager:
    """Manages the global search results cache."""

    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
        self._loaded = False

    def ensure_initialized(self) -> None:
        """Ensure cache directory exists and data is loaded."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if not self._loaded:
            self._load()

    def _load(self) -> None:
        """Load cache from disk."""
        if not SEARCHES_FILE.exists():
            self._cache = {}
            self._loaded = True
            return

        try:
            with open(SEARCHES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._cache = {}
            for query, entry_data in data.items():
                matches = [
                    SearchMatch(
                        video_id=m["video_id"],
                        title=m["title"],
                        channel=m["channel"],
                        duration=m["duration"]
                    )
                    for m in entry_data.get("matches", [])
                ]
                self._cache[query] = CacheEntry(
                    query=query,
                    status=CacheStatus(entry_data["status"]),
                    matches=matches,
                    selected=entry_data.get("selected"),
                    searched_at=datetime.fromisoformat(entry_data["searched_at"]),
                    query_used=entry_data["query_used"]
                )
            self._loaded = True
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise CacheError(f"Failed to load cache: {e}")

    def _save(self) -> None:
        """Save cache to disk."""
        data = {}
        for query, entry in self._cache.items():
            data[query] = {
                "status": entry.status.value,
                "matches": [
                    {
                        "video_id": m.video_id,
                        "title": m.title,
                        "channel": m.channel,
                        "duration": m.duration
                    }
                    for m in entry.matches
                ],
                "selected": entry.selected,
                "searched_at": entry.searched_at.isoformat(),
                "query_used": entry.query_used
            }

        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(SEARCHES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise CacheError(f"Failed to save cache: {e}")

    def get(self, query: str) -> Optional[CacheEntry]:
        """Get a cache entry by query string.

        Args:
            query: The search query (e.g., "Song - Artist").

        Returns:
            CacheEntry if found, None otherwise.
        """
        self.ensure_initialized()
        return self._cache.get(query)

    def save(self, entry: CacheEntry) -> None:
        """Save a cache entry.

        Args:
            entry: The cache entry to save.
        """
        self.ensure_initialized()
        self._cache[entry.query] = entry
        self._save()

    def get_selected_video_id(self, query: str) -> Optional[str]:
        """Get the selected video ID for a query.

        Args:
            query: The search query.

        Returns:
            Video ID if found and has selection, None otherwise.
        """
        entry = self.get(query)
        if entry is None or entry.status == CacheStatus.NOT_FOUND:
            return None
        if entry.selected is None or entry.selected >= len(entry.matches):
            return None
        return entry.matches[entry.selected].video_id

    def has(self, query: str) -> bool:
        """Check if a query is in the cache.

        Args:
            query: The search query.

        Returns:
            True if cached, False otherwise.
        """
        self.ensure_initialized()
        return query in self._cache

    def all_entries(self) -> list[CacheEntry]:
        """Get all cache entries.

        Returns:
            List of all cache entries.
        """
        self.ensure_initialized()
        return list(self._cache.values())
```

**Step 4: Run tests**

Run: `pytest tests/test_cache.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add playlist_creator/core/cache.py tests/test_cache.py
git commit -m "feat: add cache manager for search results"
```

---

## Task 6: Utilities

**Files:**
- Create: `playlist_creator/core/utils.py`
- Create: `tests/test_utils.py`

**Step 1: Write failing tests**

```python
# tests/test_utils.py
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_utils.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement utilities**

```python
# playlist_creator/core/utils.py
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
    """Build a YouTube search query for a song.

    Args:
        title: Song title.
        artist: Artist name.

    Returns:
        Formatted search query string.
    """
    return f'"{title}" "{artist}" official music video'


def format_duration(duration: str) -> str:
    """Convert ISO 8601 duration to human-readable format.

    Args:
        duration: Duration string (e.g., "PT3M45S" or already "3:45").

    Returns:
        Formatted duration (e.g., "3:45").
    """
    # Already formatted
    if re.match(r"^\d+:\d{2}(:\d{2})?$", duration):
        return duration

    # Parse ISO 8601 duration
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
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of attempts.
        base_delay: Base delay in seconds (doubles each retry).
        exceptions: Tuple of exceptions to catch and retry.

    Returns:
        Decorated function.
    """
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
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            raise RuntimeError("Unreachable")  # For type checker
        return wrapper
    return decorator


def format_track_status(
    index: int,
    total: int,
    title: str,
    artist: str,
    status_icon: str,
    detail: str = ""
) -> str:
    """Format a track status line for output.

    Args:
        index: Current track number (1-indexed).
        total: Total number of tracks.
        title: Song title.
        artist: Artist name.
        status_icon: Icon to show status.
        detail: Additional detail text.

    Returns:
        Formatted status string.
    """
    prefix = f"[{index}/{total}]"
    track_name = f"{title} - {artist}"

    lines = [f"{prefix} {track_name}"]
    if detail:
        lines.append(f"       {status_icon} {detail}")
    else:
        lines.append(f"       {status_icon}")

    return "\n".join(lines)
```

**Step 4: Run tests**

Run: `pytest tests/test_utils.py -v`
Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add playlist_creator/core/utils.py tests/test_utils.py
git commit -m "feat: add utility functions (query builder, duration formatter, retry)"
```

---

## Task 7: Logger Setup

**Files:**
- Create: `playlist_creator/core/logger.py`
- Create: `tests/test_logger.py`

**Step 1: Write failing tests**

```python
# tests/test_logger.py
"""Tests for logger setup."""
import pytest
import logging
from unittest.mock import patch
from playlist_creator.core.logger import setup_logging


class TestSetupLogging:
    def test_returns_logger(self):
        with patch("playlist_creator.core.logger.LOGS_DIR") as mock_dir:
            mock_dir.mkdir = lambda **kwargs: None
            mock_dir.__truediv__ = lambda self, x: mock_dir
            mock_dir.parent = mock_dir

            logger = setup_logging(verbose=False)

            assert isinstance(logger, logging.Logger)
            assert logger.name == "playlist_creator"

    def test_verbose_sets_debug_level(self):
        with patch("playlist_creator.core.logger.LOGS_DIR") as mock_dir:
            mock_dir.mkdir = lambda **kwargs: None
            mock_dir.__truediv__ = lambda self, x: mock_dir
            mock_dir.parent = mock_dir

            logger = setup_logging(verbose=True)

            # Check that at least one handler has DEBUG level
            has_debug_handler = any(
                h.level == logging.DEBUG
                for h in logger.handlers
                if isinstance(h, logging.StreamHandler)
            )
            assert has_debug_handler
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_logger.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement logger**

```python
# playlist_creator/core/logger.py
"""Logging configuration for YouTube Playlist Creator."""
import logging
import sys
from datetime import datetime
from pathlib import Path

from config import LOGS_DIR


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for console and file output.

    Args:
        verbose: If True, console shows DEBUG level. Otherwise INFO.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("playlist_creator")

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)

    # File handler: always DEBUG for complete history
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / f"{datetime.now():%Y-%m-%d}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s"
        ))
        logger.addHandler(file_handler)
    except OSError:
        # Can't write to log file, continue without file logging
        pass

    # Console handler: INFO or DEBUG based on verbose flag
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    return logger
```

**Step 4: Run tests**

Run: `pytest tests/test_logger.py -v`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add playlist_creator/core/logger.py tests/test_logger.py
git commit -m "feat: add logging configuration"
```

---

## Task 8: OAuth Authentication

**Files:**
- Create: `playlist_creator/core/auth.py`
- Create: `tests/test_auth.py`

**Step 1: Write failing tests**

```python
# tests/test_auth.py
"""Tests for OAuth authentication."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from playlist_creator.core.auth import (
    get_credentials,
    get_authenticated_service,
    ensure_authenticated,
)
from playlist_creator.core.exceptions import AuthenticationError


class TestGetCredentials:
    def test_raises_without_client_secrets(self, tmp_path):
        with patch("playlist_creator.core.auth.TOKEN_FILE", tmp_path / "token.json"):
            with pytest.raises(AuthenticationError) as exc_info:
                get_credentials(client_secrets_path=tmp_path / "nonexistent.json")
            assert "client_secrets.json" in str(exc_info.value)

    def test_loads_existing_token(self, tmp_path):
        token_file = tmp_path / "token.json"

        with patch("playlist_creator.core.auth.TOKEN_FILE", token_file):
            with patch("playlist_creator.core.auth.Credentials") as mock_creds_class:
                mock_creds = Mock()
                mock_creds.valid = True
                mock_creds_class.from_authorized_user_file.return_value = mock_creds

                # Create a dummy token file
                token_file.write_text('{"token": "test"}')

                result = get_credentials(client_secrets_path=tmp_path / "secrets.json")

                assert result == mock_creds


class TestEnsureAuthenticated:
    def test_decorator_triggers_auth(self):
        mock_func = Mock(return_value="result")

        with patch("playlist_creator.core.auth.get_authenticated_service") as mock_get:
            mock_get.return_value = Mock()

            @ensure_authenticated
            def my_func(youtube_service):
                return mock_func(youtube_service)

            result = my_func()

            mock_get.assert_called_once()
            assert mock_func.called
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_auth.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement auth module**

```python
# playlist_creator/core/auth.py
"""OAuth 2.0 authentication for YouTube API."""
import logging
from functools import wraps
from pathlib import Path
from typing import Optional, Callable, TypeVar

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    TOKEN_FILE,
    CREDENTIALS_DIR,
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION,
    YOUTUBE_SCOPES,
)
from playlist_creator.core.exceptions import AuthenticationError


logger = logging.getLogger("playlist_creator")

T = TypeVar("T")


def get_credentials(client_secrets_path: Optional[Path] = None) -> Credentials:
    """Get valid OAuth credentials, refreshing or re-authenticating as needed.

    Args:
        client_secrets_path: Path to client_secrets.json. If None, looks in
            current directory.

    Returns:
        Valid Credentials object.

    Raises:
        AuthenticationError: If authentication fails or client_secrets.json
            is not found.
    """
    if client_secrets_path is None:
        client_secrets_path = Path("client_secrets.json")

    creds = None

    # Load existing token if available
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), YOUTUBE_SCOPES)
        except Exception as e:
            logger.debug(f"Could not load existing token: {e}")

    # Refresh or re-authenticate if needed
    if creds and creds.expired and creds.refresh_token:
        try:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            creds = None

    if not creds or not creds.valid:
        if not client_secrets_path.exists():
            raise AuthenticationError(
                f"client_secrets.json not found at {client_secrets_path}. "
                "Download it from Google Cloud Console."
            )

        logger.info("Starting OAuth flow...")
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets_path),
                YOUTUBE_SCOPES
            )
            creds = flow.run_local_server(port=0)
        except Exception as e:
            raise AuthenticationError(f"OAuth flow failed: {e}")

        # Save token for future use
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        logger.info(f"Token saved to {TOKEN_FILE}")

    return creds


def get_authenticated_service(client_secrets_path: Optional[Path] = None):
    """Get an authenticated YouTube API service.

    Args:
        client_secrets_path: Path to client_secrets.json.

    Returns:
        Authenticated YouTube API service object.

    Raises:
        AuthenticationError: If authentication fails.
    """
    creds = get_credentials(client_secrets_path)
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)


def ensure_authenticated(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that ensures YouTube service is authenticated before calling.

    The decorated function should accept `youtube_service` as its first
    positional argument.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        if "youtube_service" not in kwargs and (not args or args[0] is None):
            kwargs["youtube_service"] = get_authenticated_service()
        return func(*args, **kwargs)
    return wrapper
```

**Step 4: Run tests**

Run: `pytest tests/test_auth.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add playlist_creator/core/auth.py tests/test_auth.py
git commit -m "feat: add OAuth authentication flow"
```

---

## Task 9: YouTube Client - Search

**Files:**
- Create: `playlist_creator/core/youtube_client.py`
- Create: `tests/test_youtube_client.py`

**Step 1: Write failing tests**

```python
# tests/test_youtube_client.py
"""Tests for YouTube API client."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from playlist_creator.core.youtube_client import YouTubeClient
from playlist_creator.models import SearchMatch, CacheEntry, CacheStatus
from playlist_creator.core.exceptions import QuotaExceededError, YouTubeAPIError


class TestYouTubeClientSearch:
    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def client(self, mock_service):
        return YouTubeClient(service=mock_service)

    def test_search_returns_matches(self, client, mock_service):
        # Mock search response
        mock_service.search().list().execute.return_value = {
            "items": [
                {
                    "id": {"videoId": "abc123"},
                    "snippet": {
                        "title": "Yeah! (Official Video)",
                        "channelTitle": "UsherVEVO"
                    }
                },
                {
                    "id": {"videoId": "def456"},
                    "snippet": {
                        "title": "Yeah! Lyrics",
                        "channelTitle": "LyricsChannel"
                    }
                }
            ]
        }

        # Mock videos.list for duration
        mock_service.videos().list().execute.return_value = {
            "items": [
                {"id": "abc123", "contentDetails": {"duration": "PT4M11S"}},
                {"id": "def456", "contentDetails": {"duration": "PT4M10S"}}
            ]
        }

        result = client.search("Yeah!", "Usher")

        assert result.status == CacheStatus.FOUND
        assert len(result.matches) == 2
        assert result.matches[0].video_id == "abc123"
        assert result.matches[0].duration == "4:11"

    def test_search_no_results(self, client, mock_service):
        mock_service.search().list().execute.return_value = {"items": []}

        result = client.search("Unknown Song", "Unknown Artist")

        assert result.status == CacheStatus.NOT_FOUND
        assert result.matches == []

    def test_search_quota_exceeded(self, client, mock_service):
        from googleapiclient.errors import HttpError

        error_response = Mock()
        error_response.status = 403
        error_response.reason = "quotaExceeded"

        mock_service.search().list().execute.side_effect = HttpError(
            resp=error_response,
            content=b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}'
        )

        with pytest.raises(QuotaExceededError):
            client.search("Test", "Artist")
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_youtube_client.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement YouTube client (search only)**

```python
# playlist_creator/core/youtube_client.py
"""YouTube API client wrapper."""
import logging
import time
from datetime import datetime
from typing import Optional

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from config import RATE_LIMIT_DELAY, MAX_SEARCH_RESULTS, MUSIC_CATEGORY_ID
from playlist_creator.core.exceptions import (
    QuotaExceededError,
    YouTubeAPIError,
    VideoUnavailableError,
    PlaylistNotFoundError,
)
from playlist_creator.core.utils import build_search_query, format_duration
from playlist_creator.models import CacheEntry, CacheStatus, SearchMatch


logger = logging.getLogger("playlist_creator")


class YouTubeClient:
    """Wrapper for YouTube Data API v3."""

    def __init__(self, service: Resource):
        """Initialize with an authenticated YouTube service.

        Args:
            service: Authenticated YouTube API service from googleapiclient.
        """
        self._service = service
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Enforce rate limiting between API requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _handle_http_error(self, error: HttpError) -> None:
        """Convert HttpError to appropriate custom exception.

        Args:
            error: The HttpError from the API.

        Raises:
            QuotaExceededError: If quota is exceeded.
            YouTubeAPIError: For other API errors.
        """
        if error.resp.status == 403:
            content = error.content.decode("utf-8", errors="ignore")
            if "quotaExceeded" in content:
                raise QuotaExceededError()
        raise YouTubeAPIError(f"YouTube API error: {error}")

    def search(self, title: str, artist: str) -> CacheEntry:
        """Search YouTube for a song.

        Args:
            title: Song title.
            artist: Artist name.

        Returns:
            CacheEntry with search results.

        Raises:
            QuotaExceededError: If API quota is exceeded.
            YouTubeAPIError: For other API errors.
        """
        query = build_search_query(title, artist)
        query_key = f"{title} - {artist}"

        self._rate_limit()

        try:
            # Search for videos
            search_response = self._service.search().list(
                q=query,
                part="id,snippet",
                type="video",
                videoCategoryId=MUSIC_CATEGORY_ID,
                maxResults=MAX_SEARCH_RESULTS
            ).execute()
        except HttpError as e:
            self._handle_http_error(e)

        items = search_response.get("items", [])

        if not items:
            return CacheEntry(
                query=query_key,
                status=CacheStatus.NOT_FOUND,
                matches=[],
                selected=None,
                searched_at=datetime.now(),
                query_used=query
            )

        # Get video IDs for duration lookup
        video_ids = [item["id"]["videoId"] for item in items]

        # Get durations
        durations = self._get_video_durations(video_ids)

        # Build matches
        matches = []
        for item in items:
            video_id = item["id"]["videoId"]
            matches.append(SearchMatch(
                video_id=video_id,
                title=item["snippet"]["title"],
                channel=item["snippet"]["channelTitle"],
                duration=durations.get(video_id, "?:??")
            ))

        return CacheEntry(
            query=query_key,
            status=CacheStatus.FOUND,
            matches=matches,
            selected=0,
            searched_at=datetime.now(),
            query_used=query
        )

    def _get_video_durations(self, video_ids: list[str]) -> dict[str, str]:
        """Get durations for a list of video IDs.

        Args:
            video_ids: List of YouTube video IDs.

        Returns:
            Dict mapping video ID to formatted duration.
        """
        if not video_ids:
            return {}

        self._rate_limit()

        try:
            response = self._service.videos().list(
                id=",".join(video_ids),
                part="contentDetails"
            ).execute()
        except HttpError as e:
            logger.warning(f"Could not fetch durations: {e}")
            return {}

        durations = {}
        for item in response.get("items", []):
            video_id = item["id"]
            iso_duration = item["contentDetails"]["duration"]
            durations[video_id] = format_duration(iso_duration)

        return durations
```

**Step 4: Run tests**

Run: `pytest tests/test_youtube_client.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add playlist_creator/core/youtube_client.py tests/test_youtube_client.py
git commit -m "feat: add YouTube client with search functionality"
```

---

## Task 10: YouTube Client - Playlist Operations

**Files:**
- Modify: `playlist_creator/core/youtube_client.py`
- Modify: `tests/test_youtube_client.py`

**Step 1: Add tests for playlist operations**

```python
# Add to tests/test_youtube_client.py

class TestYouTubeClientPlaylist:
    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def client(self, mock_service):
        return YouTubeClient(service=mock_service)

    def test_create_playlist(self, client, mock_service):
        mock_service.playlists().insert().execute.return_value = {
            "id": "PLnewplaylist123",
            "snippet": {"title": "Test Playlist"}
        }

        result = client.create_playlist("Test Playlist", privacy="private")

        assert result == "PLnewplaylist123"
        mock_service.playlists().insert.assert_called_once()

    def test_add_video_to_playlist(self, client, mock_service):
        mock_service.playlistItems().insert().execute.return_value = {
            "id": "item123"
        }

        result = client.add_video_to_playlist("PLtest", "videoABC")

        assert result == "item123"

    def test_add_video_unavailable(self, client, mock_service):
        from googleapiclient.errors import HttpError

        error_response = Mock()
        error_response.status = 404

        mock_service.playlistItems().insert().execute.side_effect = HttpError(
            resp=error_response,
            content=b'{"error": {"errors": [{"reason": "videoNotFound"}]}}'
        )

        with pytest.raises(VideoUnavailableError):
            client.add_video_to_playlist("PLtest", "deletedVideo")

    def test_get_playlist_items(self, client, mock_service):
        mock_service.playlistItems().list().execute.return_value = {
            "items": [
                {
                    "id": "item1",
                    "snippet": {
                        "resourceId": {"videoId": "vid1"},
                        "position": 0
                    }
                },
                {
                    "id": "item2",
                    "snippet": {
                        "resourceId": {"videoId": "vid2"},
                        "position": 1
                    }
                }
            ],
            "nextPageToken": None
        }

        result = client.get_playlist_items("PLtest")

        assert len(result) == 2
        assert result[0]["video_id"] == "vid1"
        assert result[1]["video_id"] == "vid2"

    def test_remove_playlist_item(self, client, mock_service):
        mock_service.playlistItems().delete().execute.return_value = {}

        client.remove_playlist_item("item123")

        mock_service.playlistItems().delete.assert_called_once()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_youtube_client.py::TestYouTubeClientPlaylist -v`
Expected: FAIL with AttributeError (methods don't exist)

**Step 3: Add playlist methods to YouTube client**

Add to `playlist_creator/core/youtube_client.py`:

```python
    def create_playlist(
        self,
        title: str,
        description: str = "",
        privacy: str = "private"
    ) -> str:
        """Create a new YouTube playlist.

        Args:
            title: Playlist title.
            description: Playlist description.
            privacy: Privacy status (private, unlisted, public).

        Returns:
            Playlist ID.

        Raises:
            QuotaExceededError: If API quota is exceeded.
            YouTubeAPIError: For other API errors.
        """
        self._rate_limit()

        try:
            response = self._service.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description
                    },
                    "status": {
                        "privacyStatus": privacy
                    }
                }
            ).execute()
        except HttpError as e:
            self._handle_http_error(e)

        return response["id"]

    def add_video_to_playlist(
        self,
        playlist_id: str,
        video_id: str,
        position: Optional[int] = None
    ) -> str:
        """Add a video to a playlist.

        Args:
            playlist_id: YouTube playlist ID.
            video_id: YouTube video ID.
            position: Position in playlist (None for end).

        Returns:
            Playlist item ID.

        Raises:
            VideoUnavailableError: If video doesn't exist or is blocked.
            QuotaExceededError: If API quota is exceeded.
            YouTubeAPIError: For other API errors.
        """
        self._rate_limit()

        body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
        if position is not None:
            body["snippet"]["position"] = position

        try:
            response = self._service.playlistItems().insert(
                part="snippet",
                body=body
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise VideoUnavailableError(video_id)
            self._handle_http_error(e)

        return response["id"]

    def get_playlist_items(self, playlist_id: str) -> list[dict]:
        """Get all items in a playlist.

        Args:
            playlist_id: YouTube playlist ID.

        Returns:
            List of dicts with video_id, item_id, and position.

        Raises:
            PlaylistNotFoundError: If playlist doesn't exist.
            QuotaExceededError: If API quota is exceeded.
            YouTubeAPIError: For other API errors.
        """
        items = []
        page_token = None

        while True:
            self._rate_limit()

            try:
                response = self._service.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=page_token
                ).execute()
            except HttpError as e:
                if e.resp.status == 404:
                    raise PlaylistNotFoundError(playlist_id)
                self._handle_http_error(e)

            for item in response.get("items", []):
                items.append({
                    "item_id": item["id"],
                    "video_id": item["snippet"]["resourceId"]["videoId"],
                    "position": item["snippet"]["position"]
                })

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return items

    def remove_playlist_item(self, item_id: str) -> None:
        """Remove an item from a playlist.

        Args:
            item_id: Playlist item ID (not video ID).

        Raises:
            QuotaExceededError: If API quota is exceeded.
            YouTubeAPIError: For other API errors.
        """
        self._rate_limit()

        try:
            self._service.playlistItems().delete(id=item_id).execute()
        except HttpError as e:
            self._handle_http_error(e)

    def update_playlist_item_position(
        self,
        playlist_id: str,
        item_id: str,
        video_id: str,
        new_position: int
    ) -> None:
        """Update the position of an item in a playlist.

        Args:
            playlist_id: YouTube playlist ID.
            item_id: Playlist item ID.
            video_id: Video ID of the item.
            new_position: New position (0-indexed).

        Raises:
            QuotaExceededError: If API quota is exceeded.
            YouTubeAPIError: For other API errors.
        """
        self._rate_limit()

        try:
            self._service.playlistItems().update(
                part="snippet",
                body={
                    "id": item_id,
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        },
                        "position": new_position
                    }
                }
            ).execute()
        except HttpError as e:
            self._handle_http_error(e)
```

**Step 4: Run tests**

Run: `pytest tests/test_youtube_client.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add playlist_creator/core/youtube_client.py tests/test_youtube_client.py
git commit -m "feat: add playlist operations to YouTube client"
```

---

## Task 11: Search Command

**Files:**
- Create: `playlist_creator/commands/__init__.py`
- Create: `playlist_creator/commands/search.py`
- Create: `tests/test_commands_search.py`

**Step 1: Write failing tests**

```python
# tests/test_commands_search.py
"""Tests for search command."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from playlist_creator.commands.search import search_command
from playlist_creator.models import CacheEntry, CacheStatus, SearchMatch


class TestSearchCommand:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def valid_md_file(self, tmp_path):
        content = """# Test Playlist

| # | Música | Artista |
|---|--------|---------|
| 1 | Yeah! | Usher |
| 2 | In Da Club | 50 Cent |
"""
        file = tmp_path / "test.md"
        file.write_text(content)
        return file

    def test_search_success(self, runner, valid_md_file):
        mock_cache = Mock()
        mock_cache.has.return_value = False
        mock_cache.get.return_value = None

        mock_youtube = Mock()
        mock_youtube.search.return_value = CacheEntry(
            query="Yeah! - Usher",
            status=CacheStatus.FOUND,
            matches=[SearchMatch("abc", "Yeah!", "UsherVEVO", "4:11")],
            selected=0,
            searched_at=MagicMock(),
            query_used='"Yeah!" "Usher" official'
        )

        with patch("playlist_creator.commands.search.CacheManager", return_value=mock_cache):
            with patch("playlist_creator.commands.search.get_authenticated_service"):
                with patch("playlist_creator.commands.search.YouTubeClient", return_value=mock_youtube):
                    result = runner.invoke(search_command, [str(valid_md_file)])

        assert result.exit_code == 0
        assert "Test Playlist" in result.output

    def test_search_skips_cached(self, runner, valid_md_file):
        mock_cache = Mock()
        mock_cache.has.return_value = True  # Already cached
        mock_cache.get.return_value = CacheEntry(
            query="Yeah! - Usher",
            status=CacheStatus.FOUND,
            matches=[SearchMatch("abc", "Yeah!", "UsherVEVO", "4:11")],
            selected=0,
            searched_at=MagicMock(),
            query_used='"Yeah!" "Usher" official'
        )

        mock_youtube = Mock()

        with patch("playlist_creator.commands.search.CacheManager", return_value=mock_cache):
            with patch("playlist_creator.commands.search.get_authenticated_service"):
                with patch("playlist_creator.commands.search.YouTubeClient", return_value=mock_youtube):
                    result = runner.invoke(search_command, [str(valid_md_file)])

        # YouTube search should not be called for cached items
        mock_youtube.search.assert_not_called()

    def test_search_file_not_found(self, runner):
        result = runner.invoke(search_command, ["/nonexistent/file.md"])
        assert result.exit_code != 0
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_commands_search.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create commands package init**

```python
# playlist_creator/commands/__init__.py
"""CLI commands for YouTube Playlist Creator."""
```

**Step 4: Implement search command**

```python
# playlist_creator/commands/search.py
"""Search command implementation."""
import logging
from pathlib import Path

import click

from playlist_creator.core.auth import get_authenticated_service
from playlist_creator.core.cache import CacheManager
from playlist_creator.core.exceptions import QuotaExceededError, PlaylistCreatorError
from playlist_creator.core.logger import setup_logging
from playlist_creator.core.parser import parse_markdown
from playlist_creator.core.utils import Icons, format_track_status
from playlist_creator.core.youtube_client import YouTubeClient
from playlist_creator.models import CacheStatus


@click.command("search")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--force", is_flag=True, help="Re-search songs already in cache")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def search_command(file: Path, force: bool, verbose: bool) -> None:
    """Search YouTube for songs in a Markdown playlist file."""
    logger = setup_logging(verbose=verbose)

    try:
        # Parse markdown
        click.echo(f"{Icons.FOLDER} Lendo: {file}")
        playlist = parse_markdown(file)
        click.echo(f"{Icons.PLAYLIST} Playlist: \"{playlist.name}\"")

        # Initialize cache
        cache = CacheManager()
        cache.ensure_initialized()

        # Count cached vs new
        cached_count = sum(1 for t in playlist.tracks if cache.has(t.query) and not force)
        new_count = len(playlist.tracks) - cached_count

        click.echo(f"{Icons.SEARCH} {len(playlist.tracks)} músicas no arquivo, {cached_count} já no cache")
        click.echo()

        if new_count == 0 and not force:
            click.echo(f"{Icons.SUCCESS} Todas as músicas já estão no cache. Use --force para re-buscar.")
            return

        # Get authenticated service
        service = get_authenticated_service()
        youtube = YouTubeClient(service)

        # Search each track
        found = 0
        not_found = 0
        skipped = 0

        for i, track in enumerate(playlist.tracks, 1):
            if cache.has(track.query) and not force:
                if verbose:
                    click.echo(format_track_status(
                        i, len(playlist.tracks),
                        track.title, track.artist,
                        Icons.SKIP, "Já no cache"
                    ))
                skipped += 1
                continue

            click.echo(f"[{i}/{len(playlist.tracks)}] {track.title} - {track.artist}")
            click.echo(f"       {Icons.SEARCH} Buscando...")

            try:
                result = youtube.search(track.title, track.artist)
                cache.save(result)

                if result.status == CacheStatus.FOUND:
                    found += 1
                    match = result.matches[0]
                    click.echo(f"       {Icons.SUCCESS} Encontrado: \"{match.title}\" ({match.duration}) [{match.channel}]")

                    if verbose and len(result.matches) > 1:
                        for j, alt in enumerate(result.matches[1:], 2):
                            click.echo(f"         Alt {j}: \"{alt.title}\" ({alt.duration}) [{alt.channel}]")
                else:
                    not_found += 1
                    click.echo(f"       {Icons.WARNING} Não encontrado")

            except QuotaExceededError as e:
                click.echo(f"\n{Icons.ERROR} {e}")
                click.echo(f"   Progresso salvo. Retome mais tarde.")
                raise SystemExit(1)

            click.echo()

        # Summary
        click.echo("─" * 40)
        click.echo(f"{Icons.SUCCESS} Busca completa")
        click.echo(f"   {found} encontradas (novas)")
        click.echo(f"   {skipped} do cache (puladas)")
        click.echo(f"   {not_found} não encontradas")
        click.echo()
        click.echo(f"{Icons.CACHED} Cache salvo")

    except PlaylistCreatorError as e:
        click.echo(f"{Icons.ERROR} {e}", err=True)
        raise SystemExit(1)
```

**Step 5: Run tests**

Run: `pytest tests/test_commands_search.py -v`
Expected: All 3 tests PASS

**Step 6: Commit**

```bash
git add playlist_creator/commands/ tests/test_commands_search.py
git commit -m "feat: add search command"
```

---

## Task 12: Create Command

**Files:**
- Create: `playlist_creator/commands/create.py`
- Create: `tests/test_commands_create.py`

**Step 1: Write failing tests**

```python
# tests/test_commands_create.py
"""Tests for create command."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from playlist_creator.commands.create import create_command
from playlist_creator.models import CacheEntry, CacheStatus, SearchMatch


class TestCreateCommand:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def valid_md_file(self, tmp_path):
        content = """# Test Playlist

| # | Música | Artista |
|---|--------|---------|
| 1 | Yeah! | Usher |
"""
        file = tmp_path / "test.md"
        file.write_text(content)
        return file

    def test_create_success(self, runner, valid_md_file):
        mock_cache = Mock()
        mock_cache.get.return_value = CacheEntry(
            query="Yeah! - Usher",
            status=CacheStatus.FOUND,
            matches=[SearchMatch("abc123", "Yeah!", "UsherVEVO", "4:11")],
            selected=0,
            searched_at=MagicMock(),
            query_used='"Yeah!" "Usher" official'
        )
        mock_cache.get_selected_video_id.return_value = "abc123"

        mock_youtube = Mock()
        mock_youtube.create_playlist.return_value = "PLnewplaylist"
        mock_youtube.add_video_to_playlist.return_value = "item1"

        with patch("playlist_creator.commands.create.CacheManager", return_value=mock_cache):
            with patch("playlist_creator.commands.create.get_authenticated_service"):
                with patch("playlist_creator.commands.create.YouTubeClient", return_value=mock_youtube):
                    result = runner.invoke(create_command, [str(valid_md_file)])

        assert result.exit_code == 0
        assert "PLnewplaylist" in result.output

    def test_create_dry_run(self, runner, valid_md_file):
        mock_cache = Mock()
        mock_cache.get.return_value = CacheEntry(
            query="Yeah! - Usher",
            status=CacheStatus.FOUND,
            matches=[SearchMatch("abc123", "Yeah!", "UsherVEVO", "4:11")],
            selected=0,
            searched_at=MagicMock(),
            query_used='"Yeah!" "Usher" official'
        )
        mock_cache.get_selected_video_id.return_value = "abc123"

        mock_youtube = Mock()

        with patch("playlist_creator.commands.create.CacheManager", return_value=mock_cache):
            with patch("playlist_creator.commands.create.get_authenticated_service"):
                with patch("playlist_creator.commands.create.YouTubeClient", return_value=mock_youtube):
                    result = runner.invoke(create_command, [str(valid_md_file), "--dry-run"])

        assert result.exit_code == 0
        # Should not create playlist in dry-run
        mock_youtube.create_playlist.assert_not_called()

    def test_create_missing_cache(self, runner, valid_md_file):
        mock_cache = Mock()
        mock_cache.get.return_value = None  # Not in cache

        with patch("playlist_creator.commands.create.CacheManager", return_value=mock_cache):
            result = runner.invoke(create_command, [str(valid_md_file)])

        assert result.exit_code != 0
        assert "search" in result.output.lower()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_commands_create.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement create command**

```python
# playlist_creator/commands/create.py
"""Create command implementation."""
import logging
from pathlib import Path
from typing import Optional

import click

from config import DEFAULT_PRIVACY
from playlist_creator.core.auth import get_authenticated_service
from playlist_creator.core.cache import CacheManager
from playlist_creator.core.exceptions import (
    QuotaExceededError,
    VideoUnavailableError,
    PlaylistCreatorError,
)
from playlist_creator.core.logger import setup_logging
from playlist_creator.core.parser import parse_markdown
from playlist_creator.core.utils import Icons
from playlist_creator.core.youtube_client import YouTubeClient
from playlist_creator.models import CacheStatus


@click.command("create")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--name", help="Custom playlist name (overrides title from file)")
@click.option("--dry-run", is_flag=True, help="Show what would be done without creating")
@click.option("--skip-missing", is_flag=True, help="Skip missing songs without confirmation")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def create_command(
    file: Path,
    name: Optional[str],
    dry_run: bool,
    skip_missing: bool,
    verbose: bool
) -> None:
    """Create a YouTube playlist from a Markdown file."""
    logger = setup_logging(verbose=verbose)

    try:
        # Parse markdown
        click.echo(f"{Icons.FOLDER} Lendo: {file}")
        playlist = parse_markdown(file)
        playlist_name = name or playlist.name
        click.echo(f"{Icons.PLAYLIST} Playlist: \"{playlist_name}\"")

        # Load cache
        cache = CacheManager()
        cache.ensure_initialized()

        # Check cache status for all tracks
        tracks_ready = []
        tracks_missing = []
        tracks_not_found = []

        for track in playlist.tracks:
            entry = cache.get(track.query)
            if entry is None:
                tracks_missing.append(track)
            elif entry.status == CacheStatus.NOT_FOUND:
                tracks_not_found.append(track)
            else:
                video_id = cache.get_selected_video_id(track.query)
                if video_id:
                    tracks_ready.append((track, video_id, entry))
                else:
                    tracks_missing.append(track)

        # Report status
        click.echo()
        click.echo(f"   {len(tracks_ready)} músicas prontas")
        click.echo(f"   {len(tracks_not_found)} não encontradas (serão puladas)")
        click.echo(f"   {len(tracks_missing)} sem cache")

        # Abort if missing cache
        if tracks_missing:
            click.echo()
            click.echo(f"{Icons.ERROR} {len(tracks_missing)} músicas não estão no cache.")
            click.echo(f"   Execute primeiro: python main.py search {file}")
            for track in tracks_missing[:5]:
                click.echo(f"   • {track.title} - {track.artist}")
            if len(tracks_missing) > 5:
                click.echo(f"   ... e mais {len(tracks_missing) - 5}")
            raise SystemExit(1)

        # Confirm if many not found
        if tracks_not_found and not skip_missing:
            pct = len(tracks_not_found) / len(playlist.tracks) * 100
            click.echo()
            click.echo(f"{Icons.WARNING} {len(tracks_not_found)} de {len(playlist.tracks)} músicas não encontradas ({pct:.0f}%)")
            if not dry_run:
                if not click.confirm("   Continuar criando playlist?"):
                    raise SystemExit(0)

        # Dry run
        if dry_run:
            click.echo()
            click.echo("─" * 40)
            click.echo("[DRY-RUN] O que seria feito:")
            click.echo(f"   • Criar playlist \"{playlist_name}\" (privada)")
            click.echo(f"   • Adicionar {len(tracks_ready)} músicas:")
            for track, video_id, _ in tracks_ready:
                click.echo(f"     [{track.position}] {track.title} - {track.artist}")
            if tracks_not_found:
                click.echo(f"   • Pular {len(tracks_not_found)} não encontradas")
            return

        # Create playlist
        click.echo()
        click.echo(f"{Icons.SEARCH} Criando playlist...")

        service = get_authenticated_service()
        youtube = YouTubeClient(service)

        playlist_id = youtube.create_playlist(playlist_name, privacy=DEFAULT_PRIVACY)
        click.echo(f"{Icons.SUCCESS} Playlist criada: https://youtube.com/playlist?list={playlist_id}")

        # Add videos
        click.echo()
        added = 0
        failed = 0

        for i, (track, video_id, entry) in enumerate(tracks_ready, 1):
            click.echo(f"[{i}/{len(tracks_ready)}] {track.title} - {track.artist}")

            try:
                youtube.add_video_to_playlist(playlist_id, video_id)
                click.echo(f"       {Icons.SUCCESS} Adicionado")
                added += 1
            except VideoUnavailableError:
                click.echo(f"       {Icons.WARNING} Vídeo indisponível - pulando")
                failed += 1
            except QuotaExceededError as e:
                click.echo(f"\n{Icons.ERROR} {e}")
                click.echo(f"   Playlist criada: https://youtube.com/playlist?list={playlist_id}")
                click.echo(f"   {added} músicas adicionadas antes do erro.")
                raise SystemExit(1)

        # Summary
        click.echo()
        click.echo("─" * 40)
        click.echo(f"{Icons.SUCCESS} Playlist criada: https://youtube.com/playlist?list={playlist_id}")
        click.echo(f"   {added}/{len(playlist.tracks)} músicas adicionadas")
        if tracks_not_found:
            click.echo(f"   {len(tracks_not_found)} não encontradas (puladas)")
        if failed:
            click.echo(f"   {failed} indisponíveis (puladas)")

    except PlaylistCreatorError as e:
        click.echo(f"{Icons.ERROR} {e}", err=True)
        raise SystemExit(1)
```

**Step 4: Run tests**

Run: `pytest tests/test_commands_create.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add playlist_creator/commands/create.py tests/test_commands_create.py
git commit -m "feat: add create command"
```

---

## Task 13: Sync Command

**Files:**
- Create: `playlist_creator/commands/sync.py`
- Create: `tests/test_commands_sync.py`

**Step 1: Write failing tests**

```python
# tests/test_commands_sync.py
"""Tests for sync command."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from playlist_creator.commands.sync import sync_command
from playlist_creator.models import CacheEntry, CacheStatus, SearchMatch


class TestSyncCommand:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def valid_md_file(self, tmp_path):
        content = """# Test Playlist

| # | Música | Artista |
|---|--------|---------|
| 1 | Yeah! | Usher |
| 2 | In Da Club | 50 Cent |
"""
        file = tmp_path / "test.md"
        file.write_text(content)
        return file

    def test_sync_dry_run(self, runner, valid_md_file):
        mock_cache = Mock()
        mock_cache.get_selected_video_id.side_effect = lambda q: {
            "Yeah! - Usher": "vid1",
            "In Da Club - 50 Cent": "vid2"
        }.get(q)
        mock_cache.get.return_value = CacheEntry(
            query="test",
            status=CacheStatus.FOUND,
            matches=[SearchMatch("vid1", "T", "C", "3:00")],
            selected=0,
            searched_at=MagicMock(),
            query_used="test"
        )

        mock_youtube = Mock()
        mock_youtube.get_playlist_items.return_value = [
            {"item_id": "item1", "video_id": "vid1", "position": 0},
            {"item_id": "item2", "video_id": "vid3", "position": 1},  # Not in md
        ]

        with patch("playlist_creator.commands.sync.CacheManager", return_value=mock_cache):
            with patch("playlist_creator.commands.sync.get_authenticated_service"):
                with patch("playlist_creator.commands.sync.YouTubeClient", return_value=mock_youtube):
                    result = runner.invoke(sync_command, [
                        str(valid_md_file),
                        "--playlist-id", "PLtest",
                        "--dry-run"
                    ])

        assert result.exit_code == 0
        assert "ADICIONAR" in result.output or "vid2" in result.output

    def test_sync_requires_playlist_id(self, runner, valid_md_file):
        result = runner.invoke(sync_command, [str(valid_md_file)])
        assert result.exit_code != 0
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_commands_sync.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement sync command**

```python
# playlist_creator/commands/sync.py
"""Sync command implementation."""
import logging
import re
from pathlib import Path
from typing import Optional

import click

from playlist_creator.core.auth import get_authenticated_service
from playlist_creator.core.cache import CacheManager
from playlist_creator.core.exceptions import (
    QuotaExceededError,
    VideoUnavailableError,
    PlaylistNotFoundError,
    PlaylistCreatorError,
)
from playlist_creator.core.logger import setup_logging
from playlist_creator.core.parser import parse_markdown
from playlist_creator.core.utils import Icons
from playlist_creator.core.youtube_client import YouTubeClient
from playlist_creator.models import CacheStatus


def extract_playlist_id(url_or_id: str) -> str:
    """Extract playlist ID from URL or return as-is if already an ID."""
    # Match playlist ID in URL
    match = re.search(r"[?&]list=([^&]+)", url_or_id)
    if match:
        return match.group(1)
    # Assume it's already an ID
    return url_or_id


@click.command("sync")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--playlist-url", help="YouTube playlist URL")
@click.option("--playlist-id", help="YouTube playlist ID")
@click.option("--remove-unknown", is_flag=True, help="Remove songs not in Markdown file")
@click.option("--dry-run", is_flag=True, help="Show what would be done without modifying")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def sync_command(
    file: Path,
    playlist_url: Optional[str],
    playlist_id: Optional[str],
    remove_unknown: bool,
    dry_run: bool,
    verbose: bool
) -> None:
    """Synchronize a YouTube playlist with a Markdown file."""
    logger = setup_logging(verbose=verbose)

    # Validate playlist identifier
    if not playlist_url and not playlist_id:
        click.echo(f"{Icons.ERROR} Especifique --playlist-url ou --playlist-id", err=True)
        raise SystemExit(1)

    pl_id = playlist_id or extract_playlist_id(playlist_url)

    try:
        # Parse markdown
        click.echo(f"{Icons.FOLDER} Lendo: {file}")
        playlist = parse_markdown(file)
        click.echo(f"{Icons.PLAYLIST} Arquivo: \"{playlist.name}\" ({len(playlist.tracks)} músicas)")

        # Load cache
        cache = CacheManager()
        cache.ensure_initialized()

        # Build desired state from markdown + cache
        desired: list[tuple] = []  # (position, track, video_id)
        missing_cache = []
        not_found = []

        for track in playlist.tracks:
            video_id = cache.get_selected_video_id(track.query)
            if video_id:
                desired.append((track.position, track, video_id))
            else:
                entry = cache.get(track.query)
                if entry and entry.status == CacheStatus.NOT_FOUND:
                    not_found.append(track)
                else:
                    missing_cache.append(track)

        if missing_cache:
            click.echo(f"\n{Icons.ERROR} {len(missing_cache)} músicas não estão no cache.")
            click.echo(f"   Execute primeiro: python main.py search {file}")
            raise SystemExit(1)

        # Sort by position
        desired.sort(key=lambda x: x[0])
        desired_video_ids = [vid for _, _, vid in desired]

        # Get current YouTube state
        click.echo(f"{Icons.SEARCH} Carregando playlist do YouTube...")

        service = get_authenticated_service()
        youtube = YouTubeClient(service)

        try:
            current_items = youtube.get_playlist_items(pl_id)
        except PlaylistNotFoundError:
            click.echo(f"{Icons.ERROR} Playlist não encontrada: {pl_id}")
            raise SystemExit(1)

        click.echo(f"{Icons.PLAYLIST} YouTube: {len(current_items)} músicas")

        # Build current state map
        current_by_video_id = {item["video_id"]: item for item in current_items}
        current_video_ids = [item["video_id"] for item in current_items]

        # Calculate changes
        to_add = []  # (position, track, video_id)
        to_remove = []  # (item_id, video_id)
        to_reorder = []  # Items that need position update
        unknown = []  # In YouTube but not in desired

        # Find what to add
        for pos, track, vid in desired:
            if vid not in current_by_video_id:
                to_add.append((pos, track, vid))

        # Find what to remove or mark as unknown
        desired_set = set(desired_video_ids)
        for item in current_items:
            if item["video_id"] not in desired_set:
                if remove_unknown:
                    to_remove.append((item["item_id"], item["video_id"]))
                else:
                    unknown.append(item)

        # Calculate reorder (items in both but wrong position)
        # This is simplified - full implementation would track all position changes

        # Report
        click.echo()
        click.echo("Alterações necessárias:")

        if to_add:
            click.echo(f"\n  ADICIONAR ({len(to_add)}):")
            for pos, track, vid in to_add:
                click.echo(f"    + {track.title} - {track.artist} (posição {pos})")

        if to_remove:
            click.echo(f"\n  REMOVER ({len(to_remove)}):")
            for item_id, vid in to_remove:
                click.echo(f"    - video_id: {vid}")

        if unknown and not remove_unknown:
            click.echo(f"\n  {Icons.WARNING} NÃO MAPEADAS ({len(unknown)}) - mantidas no final:")
            for item in unknown:
                click.echo(f"    • video_id: {item['video_id']}")
            click.echo(f"\n  Use --remove-unknown para removê-las")

        if not_found:
            click.echo(f"\n  {Icons.WARNING} NÃO ENCONTRADAS ({len(not_found)}) - serão ignoradas:")
            for track in not_found:
                click.echo(f"    • {track.title} - {track.artist}")

        if not to_add and not to_remove:
            click.echo(f"\n{Icons.SUCCESS} Playlist já está sincronizada!")
            return

        # Dry run stops here
        if dry_run:
            click.echo("\n[DRY-RUN] Nenhuma alteração feita.")
            return

        # Execute changes: Add → Reorder → Remove
        click.echo()

        # Add new videos
        if to_add:
            click.echo(f"{Icons.SEARCH} Adicionando {len(to_add)} músicas...")
            for pos, track, vid in to_add:
                try:
                    youtube.add_video_to_playlist(pl_id, vid)
                    click.echo(f"  {Icons.SUCCESS} {track.title} - {track.artist}")
                except VideoUnavailableError:
                    click.echo(f"  {Icons.WARNING} {track.title} - vídeo indisponível")
                except QuotaExceededError as e:
                    click.echo(f"\n{Icons.ERROR} {e}")
                    raise SystemExit(1)

        # Remove videos
        if to_remove:
            click.echo(f"{Icons.SEARCH} Removendo {len(to_remove)} músicas...")
            for item_id, vid in to_remove:
                try:
                    youtube.remove_playlist_item(item_id)
                    click.echo(f"  {Icons.SUCCESS} Removido: {vid}")
                except QuotaExceededError as e:
                    click.echo(f"\n{Icons.ERROR} {e}")
                    raise SystemExit(1)

        # Summary
        click.echo()
        click.echo("─" * 40)
        click.echo(f"{Icons.SUCCESS} Sincronização completa!")
        click.echo(f"   https://youtube.com/playlist?list={pl_id}")

    except PlaylistCreatorError as e:
        click.echo(f"{Icons.ERROR} {e}", err=True)
        raise SystemExit(1)
```

**Step 4: Run tests**

Run: `pytest tests/test_commands_sync.py -v`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add playlist_creator/commands/sync.py tests/test_commands_sync.py
git commit -m "feat: add sync command"
```

---

## Task 14: Main CLI Entry Point

**Files:**
- Create: `playlist_creator/main.py`
- Create: `tests/test_main.py`

**Step 1: Write failing tests**

```python
# tests/test_main.py
"""Tests for main CLI."""
import pytest
from click.testing import CliRunner

from playlist_creator.main import cli


class TestMainCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "search" in result.output
        assert "create" in result.output
        assert "sync" in result.output

    def test_search_help(self, runner):
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output

    def test_create_help(self, runner):
        result = runner.invoke(cli, ["create", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output

    def test_sync_help(self, runner):
        result = runner.invoke(cli, ["sync", "--help"])
        assert result.exit_code == 0
        assert "--playlist-url" in result.output
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement main CLI**

```python
# playlist_creator/main.py
"""Main CLI entry point for YouTube Playlist Creator."""
import click

from playlist_creator import __version__
from playlist_creator.commands.search import search_command
from playlist_creator.commands.create import create_command
from playlist_creator.commands.sync import sync_command
from playlist_creator.core.auth import get_authenticated_service
from playlist_creator.core.utils import Icons


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """YouTube Playlist Creator - Cria playlists a partir de arquivos Markdown."""
    pass


@cli.command("auth")
def auth_command() -> None:
    """Autenticar com sua conta do YouTube."""
    click.echo(f"{Icons.LOCK} Iniciando autenticação...")
    try:
        get_authenticated_service()
        click.echo(f"{Icons.SUCCESS} Autenticação concluída!")
    except Exception as e:
        click.echo(f"{Icons.ERROR} Falha na autenticação: {e}", err=True)
        raise SystemExit(1)


# Register commands
cli.add_command(search_command, "search")
cli.add_command(create_command, "create")
cli.add_command(sync_command, "sync")


if __name__ == "__main__":
    cli()
```

**Step 4: Create convenience entry point**

```python
# main.py (project root)
"""Convenience entry point for running from project root."""
from playlist_creator.main import cli

if __name__ == "__main__":
    cli()
```

**Step 5: Run tests**

Run: `pytest tests/test_main.py -v`
Expected: All 5 tests PASS

**Step 6: Commit**

```bash
git add playlist_creator/main.py main.py tests/test_main.py
git commit -m "feat: add main CLI entry point with all commands"
```

---

## Task 15: README and Example Files

**Files:**
- Create: `README.md`
- Create: `examples/test_playlist.md`

**Step 1: Create README**

```markdown
# YouTube Playlist Creator

Cria e sincroniza playlists do YouTube a partir de arquivos Markdown.

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Configuração do Google Cloud

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto
3. Ative a **YouTube Data API v3**
4. Configure a tela de consentimento OAuth:
   - User Type: Externo
   - Adicione seu email como usuário de teste
5. Crie credenciais OAuth 2.0 (tipo: Aplicativo Desktop)
6. Baixe o arquivo JSON e salve como `client_secrets.json` na raiz do projeto

## Uso

### Formato do arquivo Markdown

```markdown
# Nome da Playlist

| # | Música | Artista |
|---|--------|---------|
| 1 | Yeah! | Usher ft. Lil Jon & Ludacris |
| 2 | In Da Club | 50 Cent |
```

### Comandos

```bash
# Buscar músicas (salva no cache)
python main.py search playlist.md

# Criar playlist nova
python main.py create playlist.md

# Criar com nome customizado
python main.py create playlist.md --name "Minha Playlist"

# Sincronizar playlist existente
python main.py sync playlist.md --playlist-url "https://youtube.com/playlist?list=PLxxxxx"

# Ver o que seria feito (dry-run)
python main.py create playlist.md --dry-run
python main.py sync playlist.md --playlist-id PLxxxxx --dry-run
```

### Opções

| Comando | Opção | Descrição |
|---------|-------|-----------|
| search | --force | Re-buscar músicas já no cache |
| search | --verbose | Mostrar detalhes das buscas |
| create | --name | Nome customizado da playlist |
| create | --dry-run | Simular sem criar |
| create | --skip-missing | Pular músicas não encontradas sem confirmar |
| sync | --playlist-url | URL da playlist do YouTube |
| sync | --playlist-id | ID da playlist |
| sync | --remove-unknown | Remover músicas não mapeadas |
| sync | --dry-run | Simular sem modificar |

## Cache

O cache fica em `~/.youtube-playlist-cache/searches.json`.

Você pode editar manualmente para:
- Mudar o vídeo selecionado (campo `selected`)
- Adicionar um `video_id` para músicas não encontradas

## Limites da API

- Quota diária: 10.000 unidades
- Busca: 100 unidades
- Adicionar vídeo: 50 unidades

Uma playlist de 50 músicas usa ~7.500 unidades.

## Licença

MIT
```

**Step 2: Create example file**

```markdown
# examples/test_playlist.md
# Test Playlist

| # | Música | Artista |
|---|--------|---------|
| 1 | Bohemian Rhapsody | Queen |
| 2 | Billie Jean | Michael Jackson |
| 3 | Smells Like Teen Spirit | Nirvana |
```

**Step 3: Commit**

```bash
mkdir -p examples
git add README.md examples/
git commit -m "docs: add README and example playlist file"
```

---

## Task 16: Final Tests and Verification

**Files:**
- Run all tests

**Step 1: Run full test suite**

Run: `pytest tests/ -v --cov=playlist_creator --cov-report=term-missing`
Expected: All tests PASS with good coverage

**Step 2: Test CLI manually**

Run:
```bash
python main.py --help
python main.py search --help
python main.py create --help
python main.py sync --help
```
Expected: All help outputs display correctly

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: finalize project structure"
```

---

## Summary

| Task | Component | Files |
|------|-----------|-------|
| 1 | Project Setup | requirements.txt, config.py |
| 2 | Data Models | models/track.py |
| 3 | Exceptions | core/exceptions.py |
| 4 | Markdown Parser | core/parser.py |
| 5 | Cache Manager | core/cache.py |
| 6 | Utilities | core/utils.py |
| 7 | Logger | core/logger.py |
| 8 | OAuth Auth | core/auth.py |
| 9 | YouTube Search | core/youtube_client.py (search) |
| 10 | YouTube Playlists | core/youtube_client.py (playlist ops) |
| 11 | Search Command | commands/search.py |
| 12 | Create Command | commands/create.py |
| 13 | Sync Command | commands/sync.py |
| 14 | Main CLI | main.py |
| 15 | Documentation | README.md, examples/ |
| 16 | Verification | Full test run |
