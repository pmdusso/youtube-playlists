"""Configuration constants for YouTube Playlist Creator."""
from pathlib import Path

# Cache location
CACHE_DIR = Path.home() / ".youtube-playlist-cache"
SEARCHES_FILE = CACHE_DIR / "searches.json"
CREDENTIALS_DIR = CACHE_DIR / "credentials"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
LOGS_DIR = CACHE_DIR / "logs"
IN_PROGRESS_DIR = CACHE_DIR / ".in_progress"

# YouTube API
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
MUSIC_CATEGORY_ID = "10"

# Rate limiting
RATE_LIMIT_DELAY = 0.5  # seconds between API requests
MAX_SEARCH_RESULTS = 3  # top N matches to cache

# Retry settings
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0  # seconds

# Default playlist privacy
DEFAULT_PRIVACY = "private"
