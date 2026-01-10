"""Tests for main CLI."""
import pytest
from click.testing import CliRunner

from playlist_creator.main import cli


class TestMainCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "search" in result.output
        assert "create" in result.output
        assert "sync" in result.output

    def test_search_help(self, runner):
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output

    def test_create_help(self, runner):
        result = runner.invoke(cli, ["create", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output

    def test_sync_help(self, runner):
        result = runner.invoke(cli, ["sync", "--help"])
        assert result.exit_code == 0
        assert "--playlist-url" in result.output
