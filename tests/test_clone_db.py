"""Test cases for clone-db command."""

import os
from unittest.mock import MagicMock, patch

import pytest
import tdclient.errors
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

    def test_mutually_exclusive_options(self):
        """Test error when both skip-existing and overwrite are specified."""
        runner = CliRunner()
        result = runner.invoke(app, ["clone-db", "test_db", "--skip-existing", "--overwrite"])

        assert result.exit_code == 1
        assert "cannot be used together" in result.stderr

    @patch.dict(os.environ, {"SOURCE_API_KEY": "test_source", "DEST_API_KEY": "test_dest"})
    @patch("petit_cli.commands.clone_db.pytd.Client")
    @patch("petit_cli.commands.clone_db.validate_source_database")
    def test_skip_existing_flag(self, mock_validate_src, mock_client):
        """Test --skip-existing flag functionality."""
        runner = CliRunner()

        # Setup mock clients
        mock_source = MagicMock()
        mock_dest = MagicMock()
        mock_client.side_effect = [mock_source, mock_dest]

        # Setup validation mocks
        mock_validate_src.return_value = True

        # Setup mock table
        mock_table = MagicMock()
        mock_table.name = "test_table"
        mock_source.list_tables.return_value = [mock_table]

        result = runner.invoke(app, ["clone-db", "test_db", "--skip-existing"])

        # Should succeed
        assert result.exit_code == 0
        mock_validate_src.assert_called_once()

    @patch.dict(os.environ, {"SOURCE_API_KEY": "test_source", "DEST_API_KEY": "test_dest"})
    @patch("petit_cli.commands.clone_db.pytd.Client")
    @patch("petit_cli.commands.clone_db.validate_source_database")
    def test_overwrite_flag(self, mock_validate_src, mock_client):
        """Test --overwrite flag functionality."""
        runner = CliRunner()

        # Setup mock clients
        mock_source = MagicMock()
        mock_dest = MagicMock()
        mock_client.side_effect = [mock_source, mock_dest]

        # Setup validation mocks
        mock_validate_src.return_value = True

        # Setup mock table
        mock_table = MagicMock()
        mock_table.name = "test_table"
        mock_source.list_tables.return_value = [mock_table]

        result = runner.invoke(app, ["clone-db", "test_db", "--overwrite"])

        # Should succeed
        assert result.exit_code == 0
        mock_validate_src.assert_called_once()

    @patch.dict(os.environ, {"SOURCE_API_KEY": "test_source", "DEST_API_KEY": "test_dest"})
    @patch("petit_cli.commands.clone_db.pytd.Client")
    @patch("petit_cli.commands.clone_db.validate_source_database")
    def test_source_database_validation_failure(self, mock_validate_src, mock_client):
        """Test failure when source database validation fails."""
        runner = CliRunner()

        # Setup mock clients
        mock_source = MagicMock()
        mock_dest = MagicMock()
        mock_client.side_effect = [mock_source, mock_dest]

        # Setup validation to fail
        mock_validate_src.return_value = False

        result = runner.invoke(app, ["clone-db", "test_db"])

        assert result.exit_code == 2
        assert "Source database does not exist" in result.stderr


class TestValidationFunctions:
    """Test validation helper functions."""

    @patch("petit_cli.commands.clone_db.pytd.Client")
    def test_validate_source_database_success(self, mock_client_class):
        """Test successful source database validation."""
        from petit_cli.commands.clone_db import validate_source_database

        mock_client = MagicMock()
        mock_client.exists.return_value = True

        result = validate_source_database(mock_client, "test_db")

        assert result is True
        mock_client.exists.assert_called_once_with("test_db")

    @patch("petit_cli.commands.clone_db.pytd.Client")
    def test_validate_source_database_failure(self, mock_client_class):
        """Test source database validation failure."""
        from petit_cli.commands.clone_db import validate_source_database

        mock_client = MagicMock()
        mock_client.exists.return_value = False

        result = validate_source_database(mock_client, "test_db")

        assert result is False
        mock_client.exists.assert_called_once_with("test_db")


class TestCopyTable:
    """Test copy_table function with different table exists actions."""

    @patch("petit_cli.commands.clone_db.pd.DataFrame")
    @patch("petit_cli.commands.clone_db.pytd.table.Table")
    def test_copy_table_skip_existing(self, mock_table_class, mock_dataframe):
        """Test copy_table with skip existing action."""
        from petit_cli.commands.clone_db import TableExistsAction, copy_table

        # Setup mocks
        mock_src_client = MagicMock()
        mock_dest_client = MagicMock()
        mock_dest_client.exists.return_value = True  # Table exists
        mock_writer = MagicMock()

        # Call function with SKIP action
        copy_table(
            src_db="src_db",
            dest_db="dest_db",
            tbl_name="test_table",
            src_client=mock_src_client,
            dest_client=mock_dest_client,
            writer=mock_writer,
            table_exists_action=TableExistsAction.SKIP,
        )

        # Should not call query or write operations
        mock_src_client.query.assert_not_called()
        mock_writer.write_dataframe.assert_not_called()

    @patch("petit_cli.commands.clone_db.pd.DataFrame")
    @patch("petit_cli.commands.clone_db.pytd.table.Table")
    def test_copy_table_overwrite_existing(self, mock_table_class, mock_dataframe):
        """Test copy_table with overwrite existing action."""
        from petit_cli.commands.clone_db import TableExistsAction, copy_table

        # Setup mocks
        mock_src_client = MagicMock()
        mock_dest_client = MagicMock()
        mock_dest_client.exists.return_value = True  # Table exists
        mock_writer = MagicMock()
        mock_src_client.query.return_value = {"data": [], "columns": []}
        mock_dataframe.return_value = MagicMock()

        # Call function with OVERWRITE action
        copy_table(
            src_db="src_db",
            dest_db="dest_db",
            tbl_name="test_table",
            src_client=mock_src_client,
            dest_client=mock_dest_client,
            writer=mock_writer,
            table_exists_action=TableExistsAction.OVERWRITE,
        )

        # Should call query and write operations with overwrite
        mock_src_client.query.assert_called_once()
        mock_writer.write_dataframe.assert_called_once()
        args, kwargs = mock_writer.write_dataframe.call_args
        assert kwargs["if_exists"] == "overwrite"

    @patch("petit_cli.commands.clone_db.pd.DataFrame")
    @patch("petit_cli.commands.clone_db.pytd.table.Table")
    def test_copy_table_new_table(self, mock_table_class, mock_dataframe):
        """Test copy_table with new table (table doesn't exist)."""
        from petit_cli.commands.clone_db import TableExistsAction, copy_table

        # Setup mocks
        mock_src_client = MagicMock()
        mock_dest_client = MagicMock()
        mock_dest_client.exists.return_value = False  # Table doesn't exist
        mock_writer = MagicMock()
        mock_src_client.query.return_value = {"data": [], "columns": []}
        mock_dataframe.return_value = MagicMock()

        # Call function with any action (should copy since table doesn't exist)
        copy_table(
            src_db="src_db",
            dest_db="dest_db",
            tbl_name="test_table",
            src_client=mock_src_client,
            dest_client=mock_dest_client,
            writer=mock_writer,
            table_exists_action=TableExistsAction.ERROR,
        )

        # Should call query and write operations with error (default for new tables)
        mock_src_client.query.assert_called_once()
        mock_writer.write_dataframe.assert_called_once()
        args, kwargs = mock_writer.write_dataframe.call_args
        assert kwargs["if_exists"] == "error"

    @patch("petit_cli.commands.clone_db.pd.DataFrame")
    @patch("petit_cli.commands.clone_db.pytd.table.Table")
    def test_copy_table_auth_error(self, mock_table_class, mock_dataframe):
        """Test copy_table with authentication error."""
        from petit_cli.commands.clone_db import TableExistsAction, copy_table

        # Setup mocks
        mock_src_client = MagicMock()
        mock_dest_client = MagicMock()
        mock_dest_client.exists.return_value = False  # Table doesn't exist
        mock_writer = MagicMock()
        mock_src_client.query.return_value = {"data": [], "columns": []}
        mock_dataframe.return_value = MagicMock()

        # Make write_dataframe raise AuthError
        mock_writer.write_dataframe.side_effect = tdclient.errors.AuthError("Authentication failed")

        # Should raise AuthError
        with pytest.raises(tdclient.errors.AuthError):
            copy_table(
                src_db="src_db",
                dest_db="dest_db",
                tbl_name="test_table",
                src_client=mock_src_client,
                dest_client=mock_dest_client,
                writer=mock_writer,
                table_exists_action=TableExistsAction.ERROR,
            )

    @patch("petit_cli.commands.clone_db.pd.DataFrame")
    @patch("petit_cli.commands.clone_db.pytd.table.Table")
    def test_copy_table_forbidden_error(self, mock_table_class, mock_dataframe):
        """Test copy_table with forbidden error."""
        from petit_cli.commands.clone_db import TableExistsAction, copy_table

        # Setup mocks
        mock_src_client = MagicMock()
        mock_dest_client = MagicMock()
        mock_dest_client.exists.return_value = False  # Table doesn't exist
        mock_writer = MagicMock()
        mock_src_client.query.return_value = {"data": [], "columns": []}
        mock_dataframe.return_value = MagicMock()

        # Make write_dataframe raise ForbiddenError
        mock_writer.write_dataframe.side_effect = tdclient.errors.ForbiddenError("Access forbidden")

        # Should raise ForbiddenError
        with pytest.raises(tdclient.errors.ForbiddenError):
            copy_table(
                src_db="src_db",
                dest_db="dest_db",
                tbl_name="test_table",
                src_client=mock_src_client,
                dest_client=mock_dest_client,
                writer=mock_writer,
                table_exists_action=TableExistsAction.ERROR,
            )

    @patch("petit_cli.commands.clone_db.pd.DataFrame")
    @patch("petit_cli.commands.clone_db.pytd.table.Table")
    def test_copy_table_error_existing(self, mock_table_class, mock_dataframe):
        """Test copy_table with error action (default behavior)."""
        from petit_cli.commands.clone_db import TableExistsAction, copy_table

        # Setup mocks
        mock_src_client = MagicMock()
        mock_dest_client = MagicMock()
        mock_dest_client.exists.return_value = True  # Table exists
        mock_writer = MagicMock()

        # Call function with ERROR action (default)
        copy_table(
            src_db="src_db",
            dest_db="dest_db",
            tbl_name="test_table",
            src_client=mock_src_client,
            dest_client=mock_dest_client,
            writer=mock_writer,
            table_exists_action=TableExistsAction.ERROR,
        )

        # Should not call query or write operations (skips like before)
        mock_src_client.query.assert_not_called()
        mock_writer.write_dataframe.assert_not_called()
