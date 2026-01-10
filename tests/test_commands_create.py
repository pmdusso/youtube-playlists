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
