"""Test cases for trigger-workflow command."""

import os
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from petit_cli.commands.trigger_workflow import get_console_url, is_queue_full_error
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

        # Setup mock Attempt object with id and session_id attributes
        mock_attempt = MagicMock()
        mock_attempt.id = 99999
        mock_attempt.session_id = 67890
        mock_instance.start_attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "12345"])

        assert result.exit_code == 0
        assert "Workflow triggered successfully" in result.stdout
        assert "Workflow ID: 12345" in result.stdout
        assert "Session ID: 67890" in result.stdout
        assert "Attempt ID: 99999" in result.stdout
        assert (
            "Console URL: https://console.treasuredata.com/app/workflows/12345/sessions/67890/attempt/99999"
            in result.stdout
        )
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
        mock_attempt.workflow_id = 12345
        mock_attempt.session_id = 54321
        mock_attempt.done = True
        mock_attempt.success = True
        mock_attempt.status = "success"
        mock_attempt.finished_at = "2024-01-20T00:00:00Z"
        mock_instance.attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "--check-attempt", "67890"])

        assert result.exit_code == 0
        assert "Attempt found" in result.stdout
        assert "Status: success" in result.stdout
        assert "Console URL:" in result.stdout
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
        mock_attempt.workflow_id = 12345
        mock_attempt.session_id = 54321
        mock_attempt.done = True
        mock_attempt.success = False
        mock_attempt.status = "error"
        mock_instance.attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "--check-attempt", "67890"])

        assert result.exit_code == 1
        assert "Attempt failed" in result.stderr
        assert "Console URL:" in result.stdout

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
        mock_attempt.workflow_id = 12345
        mock_attempt.session_id = 54321
        mock_attempt.done = False
        mock_attempt.status = "running"
        mock_instance.attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "--check-attempt", "67890"])

        assert result.exit_code == 0
        assert "Attempt found" in result.stdout
        assert "Done: False" in result.stdout
        assert "Console URL:" in result.stdout

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

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_wait_keyboard_interrupt(self, mock_client):
        """Test KeyboardInterrupt handling during wait."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_12345"
        mock_attempt.done = False
        mock_attempt.status = "running"
        mock_instance.start_attempt.return_value = mock_attempt

        # Simulate KeyboardInterrupt during wait
        mock_instance.wait_attempt.side_effect = KeyboardInterrupt()

        result = runner.invoke(app, ["trigger-workflow", "12345", "--wait"])

        assert result.exit_code == 0
        assert "Stopped waiting" in result.stdout
        assert "Workflow is still running" in result.stdout

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_wait_workflow_still_running(self, mock_client):
        """Test --wait when workflow is still running after wait_attempt."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object that's still running
        mock_attempt = MagicMock()
        mock_attempt.id = "attempt_12345"
        mock_attempt.done = False
        mock_attempt.status = "running"
        mock_instance.start_attempt.return_value = mock_attempt
        mock_instance.wait_attempt.return_value = mock_attempt

        result = runner.invoke(app, ["trigger-workflow", "12345", "--wait"])

        assert result.exit_code == 0
        assert "Workflow is still running" in result.stdout
        assert "Done: False" in result.stdout

    def test_check_attempt_missing_api_key(self):
        """Test --check-attempt with missing API key."""
        runner = CliRunner()

        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, ["trigger-workflow", "--check-attempt", "67890"])
            assert result.exit_code == 2
            assert "Missing TD_API_KEY environment variable" in result.stderr

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_check_attempt_exception(self, mock_client):
        """Test exception handling in check_attempt_status."""
        runner = CliRunner()

        # Setup mock client that raises an exception
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.attempt.side_effect = Exception("Network error")

        result = runner.invoke(app, ["trigger-workflow", "--check-attempt", "67890"])

        assert result.exit_code == 1
        assert "Error: Network error" in result.stderr


class TestGetConsoleUrl:
    """Test the get_console_url function."""

    def test_production_endpoint(self):
        """Test console URL generation for production endpoint."""
        api_endpoint = "api-workflow.treasuredata.com"
        workflow_id = 12345
        session_id = 67890
        attempt_id = 11111

        result = get_console_url(api_endpoint, workflow_id, session_id, attempt_id)

        assert result == "https://console.treasuredata.com/app/workflows/12345/sessions/67890/attempt/11111"

    def test_production_endpoint_with_region(self):
        """Test console URL generation for production endpoint with region."""
        api_endpoint = "api-workflow.us01.treasuredata.com"
        workflow_id = 12345
        session_id = 67890
        attempt_id = 22222

        result = get_console_url(api_endpoint, workflow_id, session_id, attempt_id)

        assert result == "https://console.us01.treasuredata.com/app/workflows/12345/sessions/67890/attempt/22222"

    def test_development_endpoint(self):
        """Test console URL generation for development endpoint."""
        api_endpoint = "api-development-workflow.us01.treasuredata.com"
        workflow_id = 33613511
        session_id = 68444649
        attempt_id = 74441698

        result = get_console_url(api_endpoint, workflow_id, session_id, attempt_id)

        assert (
            result
            == "https://console-development.us01.treasuredata.com/app/workflows/33613511/sessions/68444649/attempt/74441698"
        )

    def test_staging_endpoint(self):
        """Test console URL generation for staging endpoint."""
        api_endpoint = "api-staging-workflow.eu01.treasuredata.com"
        workflow_id = 99999
        session_id = 11111
        attempt_id = 33333

        result = get_console_url(api_endpoint, workflow_id, session_id, attempt_id)

        assert (
            result == "https://console-staging.eu01.treasuredata.com/app/workflows/99999/sessions/11111/attempt/33333"
        )

    def test_japan_production_endpoint(self):
        """Test console URL generation for Japan production endpoint."""
        api_endpoint = "api-workflow.treasuredata.co.jp"
        workflow_id = 54321
        session_id = 98765
        attempt_id = 44444

        result = get_console_url(api_endpoint, workflow_id, session_id, attempt_id)

        assert result == "https://console.treasuredata.co.jp/app/workflows/54321/sessions/98765/attempt/44444"

    def test_unexpected_format(self):
        """Test console URL generation for unexpected endpoint format."""
        api_endpoint = "custom-endpoint.example.com"
        workflow_id = 12345
        session_id = 67890
        attempt_id = 55555

        result = get_console_url(api_endpoint, workflow_id, session_id, attempt_id)

        # Should fallback to prepending 'console-'
        assert result == "https://console-custom-endpoint.example.com/app/workflows/12345/sessions/67890/attempt/55555"


class TestIsQueueFullError:
    """Test the is_queue_full_error function."""

    def test_queue_full_error_message(self):
        """Test detection of queue full error message."""
        error = Exception("Too many attempts running. Limit: 180, Current: 250")
        assert is_queue_full_error(error) is True

    def test_400_client_error(self):
        """Test detection of 400 Client Error."""
        error = Exception(
            "400 Client Error: Bad Request for url: https://api-development-workflow.treasuredata.com/api/attempts"
        )
        assert is_queue_full_error(error) is True

    def test_combined_error_message(self):
        """Test detection of combined error message."""
        error = Exception(
            "400 Client Error: Bad Request for url: https://api-development-workflow.treasuredata.com/api/attempts\n"
            "Too many attempts running. Limit: 180, Current: 250"
        )
        assert is_queue_full_error(error) is True

    def test_non_queue_full_error(self):
        """Test non-queue-full errors are not detected."""
        error = Exception("Some other error message")
        assert is_queue_full_error(error) is False

    def test_different_error_type(self):
        """Test different error types."""
        error = Exception("Network timeout occurred")
        assert is_queue_full_error(error) is False


class TestRetryLogic:
    """Test retry logic for queue full errors."""

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    @patch("petit_cli.commands.trigger_workflow.time.sleep")
    def test_retry_on_queue_full(self, mock_sleep, mock_client):
        """Test retry on queue full error."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = 99999
        mock_attempt.session_id = 67890

        # First call raises queue full error, second succeeds
        mock_instance.start_attempt.side_effect = [
            Exception("400 Client Error: Bad Request\nToo many attempts running. Limit: 180, Current: 250"),
            mock_attempt,
        ]

        result = runner.invoke(app, ["trigger-workflow", "12345"])

        assert result.exit_code == 0
        assert "Queue is full, retrying" in result.stdout
        assert "Workflow triggered successfully" in result.stdout
        # Should have called start_attempt twice (1 failure + 1 success)
        assert mock_instance.start_attempt.call_count == 2
        # Should have slept at least once
        assert mock_sleep.call_count >= 1

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    @patch("petit_cli.commands.trigger_workflow.time.sleep")
    @patch("petit_cli.commands.trigger_workflow.time.time")
    def test_retry_gives_up_after_timeout(self, mock_time, mock_sleep, mock_client):
        """Test retry gives up after max duration."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Always raise queue full error
        mock_instance.start_attempt.side_effect = Exception(
            "400 Client Error: Bad Request\nToo many attempts running. Limit: 180, Current: 250"
        )

        # Mock time to simulate exceeding 60 seconds
        mock_time.side_effect = [0, 0, 5, 10, 20, 35, 55, 65]  # Last call exceeds 60 seconds

        result = runner.invoke(app, ["trigger-workflow", "12345"])

        assert result.exit_code == 1
        assert "Too many attempts running" in result.stderr or "400 Client Error" in result.stderr

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    def test_no_retry_on_different_error(self, mock_client):
        """Test no retry on non-queue-full errors."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Raise a different error
        mock_instance.start_attempt.side_effect = Exception("Network error")

        result = runner.invoke(app, ["trigger-workflow", "12345"])

        assert result.exit_code == 1
        assert "Error: Network error" in result.stderr
        # Should have only tried once
        assert mock_instance.start_attempt.call_count == 1

    @patch.dict(os.environ, {"TD_API_KEY": "test_api_key"})
    @patch("petit_cli.commands.trigger_workflow.Client")
    @patch("petit_cli.commands.trigger_workflow.time.sleep")
    def test_retry_with_exponential_backoff(self, mock_sleep, mock_client):
        """Test exponential backoff pattern."""
        runner = CliRunner()

        # Setup mock client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Setup mock Attempt object
        mock_attempt = MagicMock()
        mock_attempt.id = 99999
        mock_attempt.session_id = 67890

        # Fail 3 times, then succeed
        mock_instance.start_attempt.side_effect = [
            Exception("Too many attempts running"),
            Exception("Too many attempts running"),
            Exception("Too many attempts running"),
            mock_attempt,
        ]

        result = runner.invoke(app, ["trigger-workflow", "12345"])

        assert result.exit_code == 0
        # Should have slept 3 times
        assert mock_sleep.call_count == 3
        # Verify delays are increasing (exponential backoff)
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        # Delays should be increasing or capped at max_delay
        for i in range(len(sleep_calls) - 1):
            assert sleep_calls[i] <= sleep_calls[i + 1] or sleep_calls[i + 1] == 16  # max_delay
