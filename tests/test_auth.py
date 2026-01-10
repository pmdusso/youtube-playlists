"""Tests for OAuth authentication."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from playlist_creator.core.auth import (
    get_credentials,
    get_authenticated_service,
    ensure_authenticated,
)
from playlist_creator.core.exceptions import AuthenticationError


class TestGetCredentials:
    def test_raises_without_client_secrets(self, tmp_path):
        with patch("playlist_creator.core.auth.TOKEN_FILE", tmp_path / "token.json"):
            with pytest.raises(AuthenticationError) as exc_info:
                get_credentials(client_secrets_path=tmp_path / "nonexistent.json")
            assert "client_secrets.json" in str(exc_info.value)

    def test_loads_existing_token(self, tmp_path):
        token_file = tmp_path / "token.json"
        with patch("playlist_creator.core.auth.TOKEN_FILE", token_file):
            with patch("playlist_creator.core.auth.Credentials") as mock_creds_class:
                mock_creds = Mock()
                mock_creds.valid = True
                mock_creds_class.from_authorized_user_file.return_value = mock_creds
                token_file.write_text('{"token": "test"}')
                result = get_credentials(client_secrets_path=tmp_path / "secrets.json")
                assert result == mock_creds


class TestEnsureAuthenticated:
    def test_decorator_triggers_auth(self):
        mock_func = Mock(return_value="result")
        with patch("playlist_creator.core.auth.get_authenticated_service") as mock_get:
            mock_get.return_value = Mock()

            @ensure_authenticated
            def my_func(youtube_service):
                return mock_func(youtube_service)

            result = my_func()
            mock_get.assert_called_once()
            assert mock_func.called
