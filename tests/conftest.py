"""Test configuration for petit-cli."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    """Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(
        os.environ,
        {
            "TD_API_KEY": "test_td_api_key",
            "SOURCE_API_KEY": "test_source_api_key",
            "DEST_API_KEY": "test_dest_api_key",
        },
    ):
        yield


@pytest.fixture
def mock_pytd_client():
    """Mock pytd.Client for clone-db tests."""
    with patch("petit_cli.commands.clone_db.pytd.Client") as mock_client:
        # Setup mock client behavior
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Mock table listing
        mock_table = MagicMock()
        mock_table.name = "test_table"
        mock_instance.list_tables.return_value = [mock_table]

        # Mock existence check
        mock_instance.exists.return_value = False

        yield mock_client


@pytest.fixture
def mock_tdclient():
    """Mock tdclient.Client for td2parquet tests."""
    with patch("petit_cli.commands.td2parquet.tdclient.Client") as mock_client:
        # Setup mock client and job behavior
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        mock_job = MagicMock()
        mock_job.success.return_value = True
        mock_job.result_schema = [("col1", "string"), ("col2", "integer")]
        mock_job.result_format.return_value = [{"col1": "test", "col2": 123}]

        mock_instance.query.return_value = mock_job

        yield mock_client
