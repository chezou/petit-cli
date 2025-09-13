"""Test cases for clone-db command."""

import os
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from petit_cli.main import app


class TestCloneDBCommand:
    """Test the clone-db command functionality."""

    def test_missing_environment_variables(self):
        """Test error handling when environment variables are missing."""
        runner = CliRunner()

        # Test with no environment variables
        result = runner.invoke(app, ["clone-db", "test_db"])
        assert result.exit_code == 2
        assert "Missing environment variable" in result.stderr

    @patch.dict(os.environ, {"SOURCE_API_KEY": "test_source", "DEST_API_KEY": "test_dest"})
    @patch("petit_cli.commands.clone_db.pytd.Client")
    @patch("petit_cli.commands.clone_db.ThreadPoolExecutor")
    def test_successful_clone(self, mock_executor, mock_client):
        """Test successful database cloning."""
        runner = CliRunner()

        # Setup mock client
        mock_source = MagicMock()
        mock_dest = MagicMock()
        mock_client.side_effect = [mock_source, mock_dest]

        # Setup mock table
        mock_table = MagicMock()
        mock_table.name = "test_table"
        mock_source.list_tables.return_value = [mock_table]

        # Setup mock executor
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance

        result = runner.invoke(app, ["clone-db", "test_db"])

        # Should succeed
        assert result.exit_code == 0

        # Verify client creation
        assert mock_client.call_count == 2
        mock_dest.create_database_if_not_exists.assert_called_once_with("test_db")

    @patch.dict(os.environ, {"SOURCE_API_KEY": "same_key", "DEST_API_KEY": "same_key"})
    def test_same_api_keys_error(self):
        """Test error when source and destination API keys are the same."""
        runner = CliRunner()
        result = runner.invoke(app, ["clone-db", "test_db"])

        assert result.exit_code == 1
        assert "should not be the same" in result.stderr

    @patch.dict(os.environ, {"SOURCE_API_KEY": "", "DEST_API_KEY": "test_dest"})
    def test_empty_api_keys_error(self):
        """Test error when API keys are empty."""
        runner = CliRunner()
        result = runner.invoke(app, ["clone-db", "test_db"])

        assert result.exit_code == 2
        assert "should exist" in result.stderr
