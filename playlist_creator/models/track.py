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
