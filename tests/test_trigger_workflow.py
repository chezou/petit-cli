"""Test cases for trigger-workflow command."""

import os
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from petit_cli.main import app


class TestTriggerWorkflowCommand:
    """Test the trigger-workflow command functionality."""

    def test_missing_api_key(self):
        """Test error handling when TD_API_KEY is missing."""
        runner = CliRunner()

        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, ["trigger-workflow", "12345"])
            assert result.exit_code == 2
            assert "Missing TD_API_KEY environment variable" in result.stderr

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_successful_workflow_trigger(self, mock_client):
        """Test successful workflow trigger."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object with id attribute
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_12345"
        mock_instance.start_attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "12345"])

        assert result.exit_code == 0
        assert "Workflow triggered successfully" in result.stdout
        assert "Workflow ID: 12345" in result.stdout
        assert "Attempt ID: attempt_12345" in result.stdout
        mock_instance.start_attempt.assert_called_once_with(12345)

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_failed_workflow_trigger(self, mock_client):
        """Test handling of failed workflow trigger."""
        runner = CliRunner()

        # Setup mock client with None response (failure)
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.start_attempt.return_value = None

        result = runner.invoke(app, ["trigger-workflow", "12345"])

        assert result.exit_code == 1
        assert "Failed to trigger workflow" in result.stderr

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_endpoint_parameter(self, mock_client):
        """Test endpoint parameter usage."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_12345"
        mock_instance.start_attempt.return_value = mock_attempt

        # Test with custom endpoint
        result = runner.invoke(
            app,
            [
                "trigger-workflow",
                "12345",
                "--endpoint",
                "api-workflow.treasuredata.co.jp",
            ],
        )

        assert result.exit_code == 0
        # Verify client was initialized with custom endpoint
        mock_client.assert_called_once_with(apikey="test_api_key", endpoint="api-workflow.treasuredata.co.jp")

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_default_endpoint(self, mock_client):
        """Test default endpoint usage."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_12345"
        mock_instance.start_attempt.return_value = mock_attempt

        # Test without endpoint parameter (should use default)
        result = runner.invoke(app, ["trigger-workflow", "12345"])

        assert result.exit_code == 0
        # Verify client was initialized with default endpoint
        mock_client.assert_called_once_with(apikey="test_api_key", endpoint="api-workflow.treasuredata.com")

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_workflow_trigger_exception(self, mock_client):
        """Test handling of exceptions during workflow trigger."""
        runner = CliRunner()

        # Setup mock client that raises an exception
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.start_attempt.side_effect = Exception("API error")

        result = runner.invoke(app, ["trigger-workflow", "12345"])

        assert result.exit_code == 1
        assert "Error: API error" in result.stderr

    def test_workflow_id_required(self):
        """Test that workflow_id is a required argument."""
        runner = CliRunner()

        with patch.dict(os.environ, {"TD_API_KEY": "test_api_key"}):
            result = runner.invoke(app, ["trigger-workflow"])
            assert result.exit_code != 0
            # Typer will show usage/help when required argument is missing

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_workflow_id_as_integer(self, mock_client):
        """Test that workflow_id is properly parsed as integer."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_99999"
        mock_instance.start_attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "99999"])

        assert result.exit_code == 0
        # Verify the integer workflow ID was passed correctly
        mock_instance.start_attempt.assert_called_once_with(99999)

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_wait_option_success(self, mock_client):
        """Test --wait option with successful workflow completion."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_12345"
        mock_attempt.done = True
        mock_attempt.success = True
        mock_attempt.status = "success"
        mock_attempt.finished_at = "2024-01-20T00:00:00Z"
        mock_instance.start_attempt.return_value = mock_attempt
        mock_instance.wait_attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "12345", "--wait"])

        assert result.exit_code == 0
        assert "Waiting for attempt" in result.stdout
        assert "Workflow completed successfully" in result.stdout
        mock_instance.wait_attempt.assert_called_once_with(mock_attempt, wait_interval=5)

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_wait_option_failure(self, mock_client):
        """Test --wait option with failed workflow completion."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_12345"
        mock_attempt.done = True
        mock_attempt.success = False
        mock_attempt.status = "error"
        mock_attempt.finished_at = "2024-01-20T00:00:00Z"
        mock_instance.start_attempt.return_value = mock_attempt
        mock_instance.wait_attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "12345", "--wait"])

        assert result.exit_code == 1
        assert "Workflow failed" in result.stderr
        mock_instance.wait_attempt.assert_called_once_with(mock_attempt, wait_interval=5)

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_wait_option_with_custom_interval(self, mock_client):
        """Test --wait option with custom wait interval."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_12345"
        mock_attempt.done = True
        mock_attempt.success = True
        mock_attempt.status = "success"
        mock_instance.start_attempt.return_value = mock_attempt
        mock_instance.wait_attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "12345", "--wait", "--wait-interval", "10"])

        assert result.exit_code == 0
        mock_instance.wait_attempt.assert_called_once_with(mock_attempt, wait_interval=10)

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_check_attempt_success(self, mock_client):
        """Test --check-attempt option with completed attempt."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "67890"
        mock_attempt.done = True
        mock_attempt.success = True
        mock_attempt.status = "success"
        mock_attempt.finished_at = "2024-01-20T00:00:00Z"
        mock_instance.attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "--check-attempt", "67890"])

        assert result.exit_code == 0
        assert "Attempt found" in result.stdout
        assert "Status: success" in result.stdout
        mock_instance.attempt.assert_called_once_with(67890)

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_check_attempt_failed(self, mock_client):
        """Test --check-attempt option with failed attempt."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "67890"
        mock_attempt.done = True
        mock_attempt.success = False
        mock_attempt.status = "error"
        mock_instance.attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "--check-attempt", "67890"])

        assert result.exit_code == 1
        assert "Attempt failed" in result.stderr

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_check_attempt_not_found(self, mock_client):
        """Test --check-attempt option with non-existent attempt."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.attempt.return_value = None

        result = runner.invoke(app, ["trigger-workflow", "--check-attempt", "99999"])

        assert result.exit_code == 1
        assert "not found" in result.stderr

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_check_attempt_running(self, mock_client):
        """Test --check-attempt option with running attempt."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object - still running
        mock_attempt = MagicMock()
        mock_attempt.id = "67890"
        mock_attempt.done = False
        mock_attempt.status = "running"
        mock_instance.attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "--check-attempt", "67890"])

        assert result.exit_code == 0
        assert "Attempt found" in result.stdout
        assert "Done: False" in result.stdout

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_endpoint_with_https_schema(self, mock_client):
        """Test that https:// schema is automatically stripped from endpoint."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_12345"
        mock_instance.start_attempt.return_value = mock_attempt

        # Test with endpoint that includes https://
        result = runner.invoke(
            app,
            [
                "trigger-workflow",
                "12345",
                "--endpoint",
                "https://api-workflow.treasuredata.co.jp",
            ],
        )

        assert result.exit_code == 0
        # Verify client was initialized with endpoint WITHOUT https://
        mock_client.assert_called_once_with(apikey="test_api_key", endpoint="api-workflow.treasuredata.co.jp")

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_endpoint_with_http_schema(self, mock_client):
        """Test that http:// schema is automatically stripped from endpoint."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_12345"
        mock_instance.start_attempt.return_value = mock_attempt

        # Test with endpoint that includes http://
        result = runner.invoke(
            app,
            [
                "trigger-workflow",
                "12345",
                "--endpoint",
                "http://api-workflow.treasuredata.co.jp",
            ],
        )

        assert result.exit_code == 0
        # Verify client was initialized with endpoint WITHOUT http://
        mock_client.assert_called_once_with(apikey="test_api_key", endpoint="api-workflow.treasuredata.co.jp")
