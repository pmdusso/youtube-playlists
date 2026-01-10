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
