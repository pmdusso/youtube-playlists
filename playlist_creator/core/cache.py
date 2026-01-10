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
                    {"video_id": m.video_id, "title": m.title, "channel": m.channel, "duration": m.duration}
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
        """Get a cache entry by query string."""
        self.ensure_initialized()
        return self._cache.get(query)

    def save(self, entry: CacheEntry) -> None:
        """Save a cache entry."""
        self.ensure_initialized()
        self._cache[entry.query] = entry
        self._save()

    def get_selected_video_id(self, query: str) -> Optional[str]:
        """Get the selected video ID for a query."""
        entry = self.get(query)
        if entry is None or entry.status == CacheStatus.NOT_FOUND:
            return None
        if entry.selected is None or entry.selected >= len(entry.matches):
            return None
        return entry.matches[entry.selected].video_id

    def has(self, query: str) -> bool:
        """Check if a query is in the cache."""
        self.ensure_initialized()
        return query in self._cache

    def all_entries(self) -> list[CacheEntry]:
        """Get all cache entries."""
        self.ensure_initialized()
        return list(self._cache.values())
