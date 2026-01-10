# YouTube Playlist Creator - Design Document

**Date:** 2025-01-10
**Status:** Approved
**Scope:** MVP+ (search, create, sync)

---

## Problem

Creating YouTube playlists manually from a list of songs wastes time. Each song requires searching, clicking, and adding—repetitive work that a script can automate.

## Solution

A CLI tool that:
1. Parses Markdown files containing song lists
2. Searches YouTube for each song
3. Creates or synchronizes playlists via the YouTube Data API

---

## Commands

### `search` — Find songs on YouTube

```bash
python main.py search playlist.md [--force] [--verbose]
```

Searches YouTube for each song in the Markdown file. Saves the top 3 matches per song to a local cache. Skips songs already cached unless `--force` is specified.

### `create` — Build a new playlist

```bash
python main.py create playlist.md [--name "Custom Name"] [--dry-run] [--skip-missing] [--verbose]
```

Creates a private YouTube playlist using cached search results. Requires running `search` first. Prompts for confirmation if songs are missing from cache.

### `sync` — Update an existing playlist

```bash
python main.py sync playlist.md --playlist-url "https://..." [--remove-unknown] [--dry-run] [--verbose]
```

Synchronizes an existing YouTube playlist with the Markdown file. Adds new songs, removes deleted ones, reorders to match the file. Unknown songs (added manually to YouTube) stay at the end unless `--remove-unknown` is set.

### `auth` — Authenticate manually

```bash
python main.py auth
```

Runs the OAuth flow explicitly. Other commands trigger authentication automatically when needed.

---

## Input Format

The tool parses Markdown files with this structure:

```markdown
# Playlist Name

Optional description text (ignored).

| # | Música | Artista |
|---|--------|---------|
| 1 | Yeah! | Usher ft. Lil Jon & Ludacris |
| 2 | In Da Club | 50 Cent |
```

**Rules:**
- H1 heading (`#`) defines the playlist name
- Table columns must be named "Música" and "Artista"
- Column `#` determines insertion order
- Text outside tables is ignored

---

## Cache Design

### Location

```
~/.youtube-playlist-cache/
├── searches.json           # All search results
├── credentials/
│   └── token.json          # OAuth token
├── logs/
│   └── YYYY-MM-DD.log      # Daily logs
└── .in_progress/           # Recovery state
```

### Structure

Each song maps to a cache entry with up to 3 matches:

```json
{
  "Yeah! - Usher ft. Lil Jon & Ludacris": {
    "status": "found",
    "matches": [
      {
        "video_id": "GxBSyx85Kp8",
        "title": "Usher - Yeah! (Official Video) ft. Lil Jon, Ludacris",
        "channel": "UsherVEVO",
        "duration": "4:11"
      },
      {
        "video_id": "abc123",
        "title": "Yeah! (Lyrics)",
        "channel": "LyricsVids",
        "duration": "4:10"
      },
      {
        "video_id": "def456",
        "title": "Yeah! Live",
        "channel": "MTV",
        "duration": "5:23"
      }
    ],
    "selected": 0,
    "searched_at": "2025-01-10T20:30:00Z",
    "query_used": "\"Yeah!\" \"Usher ft. Lil Jon & Ludacris\" official"
  }
}
```

**Field `selected`** indexes the chosen match. Edit this value to pick a different video without re-searching.

**Status `not_found`** marks songs with no results. The tool skips these during playlist creation.

---

## Project Structure

```
playlist_creator/
├── main.py                 # CLI entry point
├── commands/
│   ├── __init__.py
│   ├── search.py
│   ├── create.py
│   └── sync.py
├── core/
│   ├── __init__.py
│   ├── parser.py           # Markdown → Track list
│   ├── cache.py            # Read/write cache
│   ├── youtube_client.py   # YouTube API wrapper
│   ├── auth.py             # OAuth 2.0 flow
│   ├── exceptions.py       # Custom exceptions
│   ├── logger.py           # Logging setup
│   └── utils.py            # Helpers
├── models/
│   ├── __init__.py
│   └── track.py            # Data classes
├── config.py               # Constants
├── requirements.txt
└── README.md
```

---

## Data Models

```python
class CacheStatus(Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"

@dataclass
class Track:
    position: int
    title: str
    artist: str

@dataclass
class SearchMatch:
    video_id: str
    title: str
    channel: str
    duration: str

@dataclass
class CacheEntry:
    query: str
    status: CacheStatus
    matches: list[SearchMatch]
    selected: int
    searched_at: datetime
    query_used: str
```

---

## Sync Algorithm

The `sync` command executes operations in this order:

1. **Add** — Insert new songs from Markdown
2. **Reorder** — Move songs to match Markdown positions
3. **Remove** — Delete songs not in Markdown (only with `--remove-unknown`)

This order ensures no data loss if the operation fails midway.

**Unknown songs** (in YouTube but not in cache) move to the playlist's end by default.

---

## Error Handling

| Error | Cause | Response |
|-------|-------|----------|
| `ParseError` | Malformed Markdown | Show line number, abort |
| `AuthenticationError` | Invalid/expired token | Attempt refresh, prompt re-auth if needed |
| `QuotaExceededError` | API daily limit hit | Save progress, show resume instructions |
| `VideoUnavailableError` | Video deleted/blocked | Skip with warning, suggest re-search |
| `PlaylistNotFoundError` | Invalid playlist URL | Show clear message |
| `YouTubeAPIError` | Other API errors | Retry 3x with backoff, then abort |

All errors save progress to allow resumption.

---

## Rate Limiting

| Operation | API Cost |
|-----------|----------|
| Search | 100 units |
| Create playlist | 50 units |
| Add video | 50 units |
| Remove video | 50 units |
| List playlist items | 1 unit |

**Daily quota:** 10,000 units (free tier)

**Strategy:**
- 0.5 second delay between requests
- On `quotaExceeded`: save state, show message with resume instructions
- In-memory quota tracking (resets per execution)

---

## Recovery

Long operations save progress to `.in_progress/`:

```json
{
  "operation": "create",
  "playlist_id": "PLxxxxx",
  "source_file": "playlist.md",
  "tracks_processed": 23,
  "tracks_total": 49,
  "started_at": "2025-01-10T20:30:00Z"
}
```

On restart, the tool detects incomplete operations and offers to resume.

---

## Dependencies

```
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.1.0
click>=8.1.0
```

---

## Future Enhancements (v2)

- `fix-missing` command for interactive resolution of not-found songs
- `cache stats`, `cache list-missing`, `cache clear` subcommands
- Support for English column headers ("Song", "Artist")
- Batch processing of multiple Markdown files
- Export playlist to Markdown (reverse operation)
