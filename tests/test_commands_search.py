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
