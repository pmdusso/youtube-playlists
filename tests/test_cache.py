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
        cache_dir = tmp_path / ".youtube-playlist-cache"
        return cache_dir

    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        with patch("playlist_creator.core.cache.CACHE_DIR", temp_cache_dir):
            with patch("playlist_creator.core.cache.SEARCHES_FILE", temp_cache_dir / "searches.json"):
                manager = CacheManager()
                yield manager

    def test_init_creates_directories(self, cache_manager, temp_cache_dir):
        cache_manager.ensure_initialized()
        assert temp_cache_dir.exists()

    def test_get_nonexistent_entry(self, cache_manager):
        cache_manager.ensure_initialized()
        result = cache_manager.get("Unknown - Artist")
        assert result is None

    def test_save_and_get_entry(self, cache_manager):
        cache_manager.ensure_initialized()
        match = SearchMatch(video_id="abc123", title="Test Video", channel="TestChannel", duration="3:45")
        entry = CacheEntry(query="Test - Artist", status=CacheStatus.FOUND, matches=[match], selected=0, searched_at=datetime(2025, 1, 10, 20, 30), query_used='"Test" "Artist" official')
        cache_manager.save(entry)
        result = cache_manager.get("Test - Artist")
        assert result is not None
        assert result.status == CacheStatus.FOUND
        assert result.matches[0].video_id == "abc123"

    def test_persistence(self, temp_cache_dir):
        with patch("playlist_creator.core.cache.CACHE_DIR", temp_cache_dir):
            with patch("playlist_creator.core.cache.SEARCHES_FILE", temp_cache_dir / "searches.json"):
                cache_manager = CacheManager()
                cache_manager.ensure_initialized()
                match = SearchMatch("xyz789", "Persisted", "Channel", "2:30")
                entry = CacheEntry(query="Persist - Test", status=CacheStatus.FOUND, matches=[match], selected=0, searched_at=datetime.now(), query_used='"Persist" "Test"')
                cache_manager.save(entry)
                new_manager = CacheManager()
                result = new_manager.get("Persist - Test")
        assert result is not None
        assert result.matches[0].video_id == "xyz789"

    def test_get_selected_video_id(self, cache_manager):
        cache_manager.ensure_initialized()
        matches = [SearchMatch("first", "First", "Ch1", "3:00"), SearchMatch("second", "Second", "Ch2", "3:01"), SearchMatch("third", "Third", "Ch3", "3:02")]
        entry = CacheEntry(query="Multi - Match", status=CacheStatus.FOUND, matches=matches, selected=1, searched_at=datetime.now(), query_used='"Multi" "Match"')
        cache_manager.save(entry)
        video_id = cache_manager.get_selected_video_id("Multi - Match")
        assert video_id == "second"

    def test_get_selected_video_id_not_found(self, cache_manager):
        cache_manager.ensure_initialized()
        entry = CacheEntry(query="Missing - Song", status=CacheStatus.NOT_FOUND, matches=[], selected=None, searched_at=datetime.now(), query_used='"Missing" "Song"')
        cache_manager.save(entry)
        video_id = cache_manager.get_selected_video_id("Missing - Song")
        assert video_id is None
