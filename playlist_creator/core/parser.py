"""Markdown parser for playlist files."""
import re
from dataclasses import dataclass
from pathlib import Path

from playlist_creator.core.exceptions import ParseError
from playlist_creator.models import Track


@dataclass
class ParsedPlaylist:
    """Result of parsing a Markdown playlist file."""
    name: str
    tracks: list[Track]


def parse_markdown(file_path: Path) -> ParsedPlaylist:
    """Parse a Markdown file into a playlist."""
    content = file_path.read_text(encoding="utf-8")
    return parse_markdown_string(content)


def parse_markdown_string(content: str) -> ParsedPlaylist:
    """Parse Markdown content string into a playlist."""
    # Extract H1 title
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if not title_match:
        raise ParseError("No H1 title found. File must start with '# Playlist Name'")

    name = title_match.group(1).strip()

    # Find all tables
    tracks = []
    table_pattern = re.compile(
        r"\|[^|]*#[^|]*\|[^|]*Música[^|]*\|[^|]*Artista[^|]*\|.*?\n"  # Header
        r"\|[-:\s|]+\n"  # Separator (only dashes, colons, spaces, and pipes)
        r"((?:\|.*?(?:\n|$))+)",  # Rows (handle end of file without newline)
        re.IGNORECASE
    )

    tables = table_pattern.findall(content)

    if not tables:
        raise ParseError(
            "No valid table found. Table must have columns: '#', 'Música', 'Artista'"
        )

    for table_rows in tables:
        for row in table_rows.strip().split("\n"):
            if not row.strip():
                continue

            cells = [cell.strip() for cell in row.split("|")]
            cells = [c for c in cells if c]

            if len(cells) >= 3:
                try:
                    position = int(cells[0])
                    title = cells[1].strip()
                    artist = cells[2].strip()
                    tracks.append(Track(position=position, title=title, artist=artist))
                except (ValueError, IndexError):
                    continue

    if not tracks:
        raise ParseError("No valid tracks found in table")

    tracks.sort(key=lambda t: t.position)

    return ParsedPlaylist(name=name, tracks=tracks)
