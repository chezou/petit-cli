"""Trigger Treasure Data Workflow."""

from __future__ import annotations

import logging
import os

import typer
from tdworkflow.attempt import Attempt  # type: ignore[import-untyped]
from tdworkflow.client import Client  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def get_api_endpoint(endpoint: str | None = None) -> str:
    """Get API endpoint.

    Args:
        endpoint: Custom endpoint (optional). If it includes a URL schema (http:// or https://),
                  it will be automatically stripped.

    Returns:
        The endpoint to use (without URL schema)
    """
    if endpoint:
        # Strip URL schema if present
        if endpoint.startswith("https://"):
            return endpoint[8:]  # Remove 'https://'
        if endpoint.startswith("http://"):
            return endpoint[7:]  # Remove 'http://'
        return endpoint

    # Default to US workflow endpoint
    return "api-workflow.treasuredata.com"


def display_attempt_status(attempt: Attempt) -> None:
    """Display attempt status information.

    Args:
        attempt: The Attempt object to display status for
    """
    typer.echo(f"  Attempt ID: {attempt.id}")
    typer.echo(f"  Status: {attempt.status}")
    typer.echo(f"  Done: {attempt.done}")

    if attempt.done:
        typer.echo(f"  Success: {attempt.success}")
        if attempt.finished_at:
            typer.echo(f"  Finished at: {attempt.finished_at}")


def wait_for_attempt(client: Client, attempt: Attempt, wait_interval: int = 5) -> Attempt:
    """Wait for an attempt to complete and show progress.

    Args:
        client: The workflow client
        attempt: The Attempt object to wait for
        wait_interval: Seconds between status checks (default: 5)

    Returns:
        The completed Attempt object
    """
    typer.echo(f"Waiting for attempt {attempt.id} to complete...")
    typer.echo("Press Ctrl+C to stop waiting (workflow will continue running)")

    try:
        # Use the client's wait_attempt method which polls automatically
        completed_attempt = client.wait_attempt(attempt, wait_interval=wait_interval)
        typer.echo()
        return completed_attempt
    except KeyboardInterrupt:
        typer.echo("\n⚠ Stopped waiting (workflow is still running)")
        # Refresh attempt status before returning
        attempt.update()
        return attempt


def check_attempt_status(
    attempt_id: str,
    endpoint: str | None = None,
) -> None:
    """Check the status of a specific workflow attempt.

    Args:
        attempt_id: The ID of the attempt to check
        endpoint: Custom endpoint URL (optional)
    """
    # Get API key from environment
    try:
        apikey = os.environ["TD_API_KEY"]
    except KeyError:
        typer.echo("Error: Missing TD_API_KEY environment variable", err=True)
        raise typer.Exit(2)

    # Get endpoint
    api_endpoint = get_api_endpoint(endpoint)

    try:
        # Create workflow client
        logger.info(f"Connecting to Treasure Data API at {api_endpoint}")
        client = Client(apikey=apikey, endpoint=api_endpoint)

        # Get attempt status
        typer.echo(f"Checking status of attempt {attempt_id}...")
        attempt = client.attempt(int(attempt_id))

        if attempt:
            typer.echo("✓ Attempt found")
            display_attempt_status(attempt)

            # Exit with appropriate code
            if attempt.done:
                if attempt.success:
                    logger.info(f"Attempt {attempt_id} completed successfully")
                else:
                    typer.echo("✗ Attempt failed", err=True)
                    logger.error(f"Attempt {attempt_id} failed")
                    raise typer.Exit(1)
        else:
            typer.echo(f"✗ Attempt {attempt_id} not found", err=True)
            logger.error(f"Attempt {attempt_id} not found")
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        logger.error(f"Error checking attempt {attempt_id}: {e}")
        raise typer.Exit(1)


def trigger_workflow_command(
    workflow_id: int = typer.Argument(None, help="ID of the workflow to trigger"),
    endpoint: str = typer.Option(None, "--endpoint", help="Treasure Data API endpoint URL (optional)"),
    wait: bool = typer.Option(False, "--wait", help="Wait for the workflow to complete"),
    wait_interval: int = typer.Option(5, "--wait-interval", help="Seconds between status checks when waiting"),
    check_attempt: str = typer.Option(None, "--check-attempt", help="Check status of a specific attempt ID"),
) -> None:
    """Trigger a Treasure Data Workflow or check attempt status.

    Environment Variables:
        TD_API_KEY: Treasure Data API key (required)

    Examples:
        # Trigger a workflow
        petit-cli trigger-workflow 12345

        # Trigger and wait for completion
        petit-cli trigger-workflow 12345 --wait

        # Check attempt status
        petit-cli trigger-workflow --check-attempt 67890

        # Custom endpoint
        petit-cli trigger-workflow 12345 --endpoint api-workflow.treasuredata.co.jp
    """
    # Check if user wants to check attempt status
    if check_attempt:
        check_attempt_status(check_attempt, endpoint)
        return

    # Workflow ID is required for triggering
    if workflow_id is None:
        typer.echo("Error: workflow_id is required when not using --check-attempt", err=True)
        raise typer.Exit(1)
    # Get API key from environment
    try:
        apikey = os.environ["TD_API_KEY"]
    except KeyError:
        typer.echo("Error: Missing TD_API_KEY environment variable", err=True)
        raise typer.Exit(2)

    # Get endpoint
    api_endpoint = get_api_endpoint(endpoint)

    try:
        # Create workflow client
        logger.info(f"Connecting to Treasure Data API at {api_endpoint}")
        client = Client(apikey=apikey, endpoint=api_endpoint)

        # Trigger the workflow
        logger.info(f"Triggering workflow ID: {workflow_id}")
        typer.echo(f"Triggering workflow {workflow_id}...")

        # Start the workflow (returns an Attempt object)
        attempt = client.start_attempt(workflow_id)

        # Display result
        if attempt:
            typer.echo("✓ Workflow triggered successfully")
            typer.echo(f"  Workflow ID: {workflow_id}")
            typer.echo(f"  Attempt ID: {attempt.id}")
            logger.info(f"Workflow {workflow_id} triggered with attempt ID {attempt.id}")

            # Wait for completion if requested
            if wait:
                typer.echo()
                attempt = wait_for_attempt(client, attempt, wait_interval)
                typer.echo()
                if attempt.done:
                    if attempt.success:
                        typer.echo("✓ Workflow completed successfully")
                        display_attempt_status(attempt)
                    else:
                        typer.echo("✗ Workflow failed", err=True)
                        display_attempt_status(attempt)
                        raise typer.Exit(1)
                else:
                    typer.echo("⚠ Workflow is still running")
                    display_attempt_status(attempt)
        else:
            typer.echo("✗ Failed to trigger workflow", err=True)
            logger.error(f"Failed to trigger workflow {workflow_id}")
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        logger.error(f"Error triggering workflow {workflow_id}: {e}")
        raise typer.Exit(1)
