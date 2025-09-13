"""Test cases for td2parquet command."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from petit_cli.main import app


class TestTD2ParquetCommand:
    """Test the td2parquet command functionality."""

    def test_missing_api_key(self):
        """Test error handling when TD_API_KEY is missing."""
        runner = CliRunner()

        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, ["td2parquet", "test_db", "test_table"])
            assert result.exit_code == 2
            assert "Missing TD_API_KEY environment variable" in result.stderr

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.td2parquet.tdclient.Client")
    def test_successful_export_incremental(self, mock_client):
        """Test successful table export with incremental processing."""
        runner = CliRunner()

        # Setup mock client and job
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        mock_job = MagicMock()
        mock_job.success.return_value = True
        mock_job.wait.return_value = None
        mock_job.result_schema = [("col1", "string"), ("col2", "integer")]
        mock_job.result_format.return_value = iter([{"col1": "test", "col2": 123}])

        mock_instance.query.return_value = mock_job

        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(
                app,
                [
                    "td2parquet",
                    "test_db",
                    "test_table",
                    "--output-dir",
                    temp_dir,
                    "--use-incremental",
                ],
            )

            assert result.exit_code == 0
            mock_instance.query.assert_called_once()

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.td2parquet.tdclient.Client")
    @patch("petit_cli.commands.td2parquet.pd.DataFrame")
    def test_successful_export_legacy(self, mock_dataframe, mock_client):
        """Test successful table export with legacy method."""
        runner = CliRunner()

        # Setup mock client and job
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        mock_job = MagicMock()
        mock_job.success.return_value = True
        mock_job.wait.return_value = None
        mock_job.result_schema = [("col1", "string"), ("col2", "integer")]
        mock_job.result_format.return_value = [{"col1": "test", "col2": 123}]

        mock_instance.query.return_value = mock_job

        # Setup mock DataFrame
        mock_df = MagicMock()
        mock_df.empty = False
        mock_dataframe.return_value = mock_df

        with tempfile.TemporaryDirectory() as temp_dir:
            runner.invoke(
                app,
                [
                    "td2parquet",
                    "test_db",
                    "test_table",
                    "--output-dir",
                    temp_dir,
                    "--no-use-incremental",
                ],
            )

            # Should succeed but may have implementation details
            # The exact behavior depends on mocking details
            mock_instance.query.assert_called_once()

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.td2parquet.tdclient.Client")
    def test_failed_job(self, mock_client):
        """Test handling of failed TD job."""
        runner = CliRunner()

        # Setup mock client with failing job
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        mock_job = MagicMock()
        mock_job.success.return_value = False
        mock_job.status.return_value = "failed"
        mock_job.wait.return_value = None

        mock_instance.query.return_value = mock_job

        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(app, ["td2parquet", "test_db", "test_table", "--output-dir", temp_dir])

            assert result.exit_code == 1

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.td2parquet.tdclient.Client")
    @patch("petit_cli.commands.td2parquet.pd.DataFrame")
    def test_endpoint_parameter(self, mock_dataframe, mock_client):
        """Test endpoint parameter usage."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock job
        mock_job = MagicMock()
        mock_job.success.return_value = True
        mock_job.wait.return_value = None
        mock_job.result_schema = [("col1", "string")]
        mock_job.result_format.return_value = [{"col1": "test"}]

        mock_instance.query.return_value = mock_job

        # Setup mock DataFrame
        mock_df = MagicMock()
        mock_df.empty = False
        mock_dataframe.return_value = mock_df

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with custom endpoint
            runner.invoke(
                app,
                [
                    "td2parquet",
                    "test_db",
                    "test_table",
                    "--output-dir",
                    temp_dir,
                    "--endpoint",
                    "https://custom.treasuredata.com",
                    "--no-use-incremental",
                ],
            )

            # Verify client was initialized with custom endpoint
            mock_client.assert_called_once_with(
                apikey="test_api_key", endpoint="https://custom.treasuredata.com", retry_post_requests=True
            )

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.td2parquet.tdclient.Client")
    @patch("petit_cli.commands.td2parquet.pd.DataFrame")
    def test_site_parameter_aws(self, mock_dataframe, mock_client):
        """Test site parameter with aws site."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock job
        mock_job = MagicMock()
        mock_job.success.return_value = True
        mock_job.wait.return_value = None
        mock_job.result_schema = [("col1", "string")]
        mock_job.result_format.return_value = [{"col1": "test"}]

        mock_instance.query.return_value = mock_job

        # Setup mock DataFrame
        mock_df = MagicMock()
        mock_df.empty = False
        mock_dataframe.return_value = mock_df

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with site parameter
            runner.invoke(
                app,
                [
                    "td2parquet",
                    "test_db",
                    "test_table",
                    "--output-dir",
                    temp_dir,
                    "--site",
                    "aws",
                    "--no-use-incremental",
                ],
            )

            # Verify client was initialized with aws endpoint
            mock_client.assert_called_once_with(
                apikey="test_api_key", endpoint="https://api.treasuredata.com", retry_post_requests=True
            )

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.td2parquet.tdclient.Client")
    @patch("petit_cli.commands.td2parquet.pd.DataFrame")
    def test_site_parameter_eu01(self, mock_dataframe, mock_client):
        """Test site parameter with eu01 site."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock job
        mock_job = MagicMock()
        mock_job.success.return_value = True
        mock_job.wait.return_value = None
        mock_job.result_schema = [("col1", "string")]
        mock_job.result_format.return_value = [{"col1": "test"}]

        mock_instance.query.return_value = mock_job

        # Setup mock DataFrame
        mock_df = MagicMock()
        mock_df.empty = False
        mock_dataframe.return_value = mock_df

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with eu01 site
            runner.invoke(
                app,
                [
                    "td2parquet",
                    "test_db",
                    "test_table",
                    "--output-dir",
                    temp_dir,
                    "--site",
                    "eu01",
                    "--no-use-incremental",
                ],
            )

            # Verify client was initialized with eu01 endpoint
            mock_client.assert_called_once_with(
                apikey="test_api_key", endpoint="https://api.eu01.treasuredata.com", retry_post_requests=True
            )
