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
