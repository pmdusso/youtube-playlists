"""YouTube API client for search and playlist operations."""
import json
import logging
import time
from datetime import datetime
from typing import Optional

from googleapiclient.errors import HttpError

from config import (
    RATE_LIMIT_DELAY,
    MAX_SEARCH_RESULTS,
    MUSIC_CATEGORY_ID,
    DEFAULT_PRIVACY,
)
from playlist_creator.core.exceptions import (
    QuotaExceededError,
    YouTubeAPIError,
    VideoUnavailableError,
)
from playlist_creator.core.utils import build_search_query, format_duration
from playlist_creator.models import CacheEntry, CacheStatus, SearchMatch


logger = logging.getLogger("playlist_creator")


class YouTubeClient:
    """Client for YouTube Data API v3 operations."""

    def __init__(self, service):
        """Initialize the YouTube client.

        Args:
            service: An authenticated YouTube API service instance.
        """
        self.service = service
        self._last_request_time: Optional[float] = None

    def _rate_limit(self) -> None:
        """Enforce rate limiting between API requests."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < RATE_LIMIT_DELAY:
                time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _handle_http_error(self, error: HttpError, video_id: Optional[str] = None) -> None:
        """Handle HTTP errors from the YouTube API.

        Args:
            error: The HttpError from the API.
            video_id: Optional video ID for VideoUnavailableError context.

        Raises:
            QuotaExceededError: If the API quota has been exceeded.
            VideoUnavailableError: If a video is not found or unavailable.
            YouTubeAPIError: For other API errors.
        """
        try:
            error_content = json.loads(error.content.decode("utf-8"))
            errors = error_content.get("error", {}).get("errors", [])
            reason = errors[0].get("reason", "") if errors else ""
        except (json.JSONDecodeError, KeyError, IndexError):
            reason = ""

        if error.resp.status == 403 and reason in ("quotaExceeded", "dailyLimitExceeded"):
            raise QuotaExceededError()

        if error.resp.status == 404 and reason == "videoNotFound":
            raise VideoUnavailableError(video_id=video_id or "unknown")

        raise YouTubeAPIError(f"YouTube API error: {error}")

    def search(self, title: str, artist: str) -> CacheEntry:
        """Search YouTube for a song.

        Args:
            title: The song title.
            artist: The artist name.

        Returns:
            A CacheEntry with search results.

        Raises:
            QuotaExceededError: If the API quota has been exceeded.
            YouTubeAPIError: For other API errors.
        """
        query = build_search_query(title, artist)
        self._rate_limit()

        try:
            search_response = self.service.search().list(
                q=query,
                part="snippet",
                type="video",
                videoCategoryId=MUSIC_CATEGORY_ID,
                maxResults=MAX_SEARCH_RESULTS,
            ).execute()
        except HttpError as e:
            self._handle_http_error(e)

        items = search_response.get("items", [])

        if not items:
            return CacheEntry(
                query=f"{title} - {artist}",
                status=CacheStatus.NOT_FOUND,
                matches=[],
                selected=None,
                searched_at=datetime.now(),
                query_used=query,
            )

        # Get video IDs for duration lookup
        video_ids = [item["id"]["videoId"] for item in items]
        durations = self._get_video_durations(video_ids)

        matches = []
        for item in items:
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            duration = durations.get(video_id, "")

            matches.append(SearchMatch(
                video_id=video_id,
                title=snippet["title"],
                channel=snippet["channelTitle"],
                duration=duration,
            ))

        return CacheEntry(
            query=f"{title} - {artist}",
            status=CacheStatus.FOUND,
            matches=matches,
            selected=0,
            searched_at=datetime.now(),
            query_used=query,
        )

    def _get_video_durations(self, video_ids: list[str]) -> dict[str, str]:
        """Get video durations for a list of video IDs.

        Args:
            video_ids: List of YouTube video IDs.

        Returns:
            A dictionary mapping video IDs to formatted duration strings.
        """
        if not video_ids:
            return {}

        self._rate_limit()

        try:
            response = self.service.videos().list(
                part="contentDetails",
                id=",".join(video_ids),
            ).execute()
        except HttpError as e:
            self._handle_http_error(e)
            return {}

        durations = {}
        for item in response.get("items", []):
            video_id = item["id"]
            iso_duration = item.get("contentDetails", {}).get("duration", "")
            durations[video_id] = format_duration(iso_duration)

        return durations

    def create_playlist(
        self,
        title: str,
        description: str = "",
        privacy: str = DEFAULT_PRIVACY,
    ) -> str:
        """Create a new YouTube playlist.

        Args:
            title: The playlist title.
            description: The playlist description.
            privacy: The privacy status ("public", "private", or "unlisted").

        Returns:
            The ID of the created playlist.

        Raises:
            QuotaExceededError: If the API quota has been exceeded.
            YouTubeAPIError: For other API errors.
        """
        self._rate_limit()

        try:
            response = self.service.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description,
                    },
                    "status": {
                        "privacyStatus": privacy,
                    },
                },
            ).execute()
        except HttpError as e:
            self._handle_http_error(e)

        return response["id"]

    def add_video_to_playlist(
        self,
        playlist_id: str,
        video_id: str,
        position: Optional[int] = None,
    ) -> str:
        """Add a video to a playlist.

        Args:
            playlist_id: The playlist ID.
            video_id: The video ID to add.
            position: Optional position in the playlist (0-indexed).

        Returns:
            The ID of the created playlist item.

        Raises:
            VideoUnavailableError: If the video is not found or unavailable.
            QuotaExceededError: If the API quota has been exceeded.
            YouTubeAPIError: For other API errors.
        """
        self._rate_limit()

        body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id,
                },
            },
        }

        if position is not None:
            body["snippet"]["position"] = position

        try:
            response = self.service.playlistItems().insert(
                part="snippet",
                body=body,
            ).execute()
        except HttpError as e:
            self._handle_http_error(e, video_id=video_id)

        return response["id"]

    def get_playlist_items(self, playlist_id: str) -> list[dict]:
        """Get all items in a playlist.

        Args:
            playlist_id: The playlist ID.

        Returns:
            A list of dictionaries with item_id, video_id, and position.

        Raises:
            QuotaExceededError: If the API quota has been exceeded.
            YouTubeAPIError: For other API errors.
        """
        items = []
        page_token = None

        while True:
            self._rate_limit()

            try:
                response = self.service.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=page_token,
                ).execute()
            except HttpError as e:
                self._handle_http_error(e)

            for item in response.get("items", []):
                snippet = item["snippet"]
                items.append({
                    "item_id": item["id"],
                    "video_id": snippet["resourceId"]["videoId"],
                    "position": snippet["position"],
                })

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return items

    def remove_playlist_item(self, item_id: str) -> None:
        """Remove an item from a playlist.

        Args:
            item_id: The playlist item ID to remove.

        Raises:
            QuotaExceededError: If the API quota has been exceeded.
            YouTubeAPIError: For other API errors.
        """
        self._rate_limit()

        try:
            self.service.playlistItems().delete(id=item_id).execute()
        except HttpError as e:
            self._handle_http_error(e)

    def update_playlist_item_position(
        self,
        playlist_id: str,
        item_id: str,
        video_id: str,
        new_position: int,
    ) -> None:
        """Update the position of an item in a playlist.

        Args:
            playlist_id: The playlist ID.
            item_id: The playlist item ID.
            video_id: The video ID.
            new_position: The new position (0-indexed).

        Raises:
            QuotaExceededError: If the API quota has been exceeded.
            YouTubeAPIError: For other API errors.
        """
        self._rate_limit()

        try:
            self.service.playlistItems().update(
                part="snippet",
                body={
                    "id": item_id,
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                        "position": new_position,
                    },
                },
            ).execute()
        except HttpError as e:
            self._handle_http_error(e)
