"""Tests for logger setup."""
import pytest
import logging
from unittest.mock import patch
from playlist_creator.core.logger import setup_logging


class TestSetupLogging:
    def test_returns_logger(self):
        with patch("playlist_creator.core.logger.LOGS_DIR") as mock_dir:
            mock_dir.mkdir = lambda **kwargs: None
            mock_dir.__truediv__ = lambda self, x: mock_dir
            mock_dir.parent = mock_dir

            logger = setup_logging(verbose=False)

            assert isinstance(logger, logging.Logger)
            assert logger.name == "playlist_creator"

    def test_verbose_sets_debug_level(self):
        with patch("playlist_creator.core.logger.LOGS_DIR") as mock_dir:
            mock_dir.mkdir = lambda **kwargs: None
            mock_dir.__truediv__ = lambda self, x: mock_dir
            mock_dir.parent = mock_dir

            logger = setup_logging(verbose=True)

            has_debug_handler = any(
                h.level == logging.DEBUG
                for h in logger.handlers
                if isinstance(h, logging.StreamHandler)
            )
            assert has_debug_handler
