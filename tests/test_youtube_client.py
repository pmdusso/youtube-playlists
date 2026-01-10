"""Tests for YouTube API client."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from playlist_creator.core.youtube_client import YouTubeClient
from playlist_creator.models import SearchMatch, CacheEntry, CacheStatus
from playlist_creator.core.exceptions import QuotaExceededError, YouTubeAPIError, VideoUnavailableError


class TestYouTubeClientSearch:
    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def client(self, mock_service):
        return YouTubeClient(service=mock_service)

    def test_search_returns_matches(self, client, mock_service):
        mock_service.search().list().execute.return_value = {
            "items": [
                {"id": {"videoId": "abc123"}, "snippet": {"title": "Yeah! (Official Video)", "channelTitle": "UsherVEVO"}},
                {"id": {"videoId": "def456"}, "snippet": {"title": "Yeah! Lyrics", "channelTitle": "LyricsChannel"}}
            ]
        }
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
        mock_service.search().list().execute.side_effect = HttpError(
            resp=error_response, content=b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}'
        )
        with pytest.raises(QuotaExceededError):
            client.search("Test", "Artist")


class TestYouTubeClientPlaylist:
    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def client(self, mock_service):
        return YouTubeClient(service=mock_service)

    def test_create_playlist(self, client, mock_service):
        mock_service.playlists().insert().execute.return_value = {"id": "PLnewplaylist123", "snippet": {"title": "Test"}}
        result = client.create_playlist("Test Playlist", privacy="private")
        assert result == "PLnewplaylist123"

    def test_add_video_to_playlist(self, client, mock_service):
        mock_service.playlistItems().insert().execute.return_value = {"id": "item123"}
        result = client.add_video_to_playlist("PLtest", "videoABC")
        assert result == "item123"

    def test_add_video_unavailable(self, client, mock_service):
        from googleapiclient.errors import HttpError
        error_response = Mock()
        error_response.status = 404
        mock_service.playlistItems().insert().execute.side_effect = HttpError(
            resp=error_response, content=b'{"error": {"errors": [{"reason": "videoNotFound"}]}}'
        )
        with pytest.raises(VideoUnavailableError):
            client.add_video_to_playlist("PLtest", "deletedVideo")

    def test_get_playlist_items(self, client, mock_service):
        mock_service.playlistItems().list().execute.return_value = {
            "items": [
                {"id": "item1", "snippet": {"resourceId": {"videoId": "vid1"}, "position": 0}},
                {"id": "item2", "snippet": {"resourceId": {"videoId": "vid2"}, "position": 1}}
            ],
            "nextPageToken": None
        }
        result = client.get_playlist_items("PLtest")
        assert len(result) == 2
        assert result[0]["video_id"] == "vid1"

    def test_remove_playlist_item(self, client, mock_service):
        mock_service.playlistItems().delete().execute.return_value = {}
        client.remove_playlist_item("item123")
        mock_service.playlistItems().delete.assert_called_with(id="item123")
