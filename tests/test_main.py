"""Test cases for main CLI functionality."""

from unittest.mock import patch

from typer.testing import CliRunner

from petit_cli.main import app


class TestMainCLI:
    """Test the main CLI application."""

    def test_version_option(self):
        """Test the --version option."""
        runner = CliRunner()

        # Mock the version retrieval to avoid PackageNotFoundError
        with patch("importlib.metadata.version", return_value="0.0.1"):
            result = runner.invoke(app, ["--version"])

            # Version command should exit with code 0 and show version
            assert result.exit_code == 0
            assert "petit-cli 0.0.1" in result.stdout
