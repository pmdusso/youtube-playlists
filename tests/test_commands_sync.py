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
