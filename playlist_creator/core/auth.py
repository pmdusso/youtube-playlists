"""OAuth 2.0 authentication for YouTube API."""
import logging
from functools import wraps
from pathlib import Path
from typing import Optional, Callable, TypeVar

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    TOKEN_FILE,
    CREDENTIALS_DIR,
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION,
    YOUTUBE_SCOPES,
)
from playlist_creator.core.exceptions import AuthenticationError


logger = logging.getLogger("playlist_creator")

T = TypeVar("T")


def get_credentials(client_secrets_path: Optional[Path] = None) -> Credentials:
    """Get valid OAuth credentials, refreshing or re-authenticating as needed."""
    if client_secrets_path is None:
        client_secrets_path = Path("client_secrets.json")

    creds = None

    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), YOUTUBE_SCOPES)
        except Exception as e:
            logger.debug(f"Could not load existing token: {e}")

    if creds and creds.expired and creds.refresh_token:
        try:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            creds = None

    if not creds or not creds.valid:
        if not client_secrets_path.exists():
            raise AuthenticationError(
                f"client_secrets.json not found at {client_secrets_path}. "
                "Download it from Google Cloud Console."
            )

        logger.info("Starting OAuth flow...")
        try:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), YOUTUBE_SCOPES)
            creds = flow.run_local_server(port=0)
        except Exception as e:
            raise AuthenticationError(f"OAuth flow failed: {e}")

        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        logger.info(f"Token saved to {TOKEN_FILE}")

    return creds


def get_authenticated_service(client_secrets_path: Optional[Path] = None):
    """Get an authenticated YouTube API service."""
    creds = get_credentials(client_secrets_path)
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)


def ensure_authenticated(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that ensures YouTube service is authenticated before calling."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        if "youtube_service" not in kwargs and (not args or args[0] is None):
            kwargs["youtube_service"] = get_authenticated_service()
        return func(*args, **kwargs)
    return wrapper
