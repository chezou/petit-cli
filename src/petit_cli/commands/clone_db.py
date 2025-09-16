"""Clone/copy databases between Treasure Data instances."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Any

import pandas as pd
import pytd  # type: ignore[import-untyped]
import tdclient  # type: ignore[import-untyped]
import tdclient.errors  # type: ignore[import-untyped]
import typer
from tqdm import tqdm

logger = logging.getLogger(__name__)
logging.getLogger("pytd.query_engine").setLevel(logging.ERROR)


class TableExistsAction(str, Enum):
    """Actions to take when a table already exists in destination."""

    ERROR = "error"
    SKIP = "skip"
    OVERWRITE = "overwrite"


def clone_db_command(
    database: str = typer.Argument(..., help="Name of the source database to clone"),
    source_endpoint: str = typer.Option(
        "https://api.treasuredata.com/",
        "--se",
        "--source-endpoint",
        help="Source Treasure Data endpoint URL",
    ),
    dest_endpoint: str = typer.Option(
        "https://api.treasuredata.com/",
        "--de",
        "--dest-endpoint",
        help="Destination Treasure Data endpoint URL",
    ),
    new_db: str | None = typer.Option(
        None,
        "--new-db",
        help="New database name in destination. Default: Same as source database name",
    ),
    skip_existing: bool = typer.Option(
        False,
        "--skip-existing",
        help="Skip tables that already exist in destination",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing tables in destination",
    ),
    table_parallelism: int = typer.Option(
        2,
        "--table-parallelism",
        help="Number of tables to process in parallel",
    ),
    download_parallelism: int = typer.Option(
        4,
        "--download-parallelism",
        help="Number of parallel download threads per table",
    ),
    chunk_size: int = typer.Option(
        100_000,
        "--chunk-size",
        help="Number of rows to process in each chunk",
    ),
    progress: bool = typer.Option(
        True,
        "--progress/--no-progress",
        help="Enable/disable detailed progress reporting with ETA calculations",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without actually performing the operation",
    ),
) -> None:
    """Clone/copy databases between Treasure Data instances.

    Environment Variables:
        SOURCE_API_KEY: API key for source Treasure Data instance
        DEST_API_KEY: API key for destination Treasure Data instance
    """
    # Validate mutually exclusive options
    if skip_existing and overwrite:
        typer.echo("Error: --skip-existing and --overwrite cannot be used together", err=True)
        raise typer.Exit(1)

    # Determine table exists action
    if skip_existing:
        table_exists_action = TableExistsAction.SKIP
    elif overwrite:
        table_exists_action = TableExistsAction.OVERWRITE
    else:
        table_exists_action = TableExistsAction.ERROR

    try:
        source_api_key = os.environ["SOURCE_API_KEY"]
        dest_api_key = os.environ["DEST_API_KEY"]
    except KeyError as e:
        typer.echo(f"Error: Missing environment variable {e}", err=True)
        raise typer.Exit(2)

    if source_api_key == dest_api_key:
        typer.echo("Error: SOURCE_API_KEY and DEST_API_KEY should not be the same", err=True)
        raise typer.Exit(1)

    if not source_api_key or not dest_api_key:
        typer.echo("Error: SOURCE_API_KEY and DEST_API_KEY should exist", err=True)
        raise typer.Exit(2)

    source_client = pytd.Client(database=database, apikey=source_api_key, endpoint=source_endpoint)  # type: ignore[attr-defined]
    dest_client = pytd.Client(apikey=dest_api_key, endpoint=dest_endpoint)  # type: ignore[attr-defined]

    if not validate_source_database(source_client, database):
        typer.echo(
            "Error: Source database does not exist or access denied. "
            "Please verify your API key and source endpoint configuration.",
            err=True,
        )
        raise typer.Exit(2)

    writer = pytd.writer.BulkImportWriter()  # type: ignore[attr-defined]

    if not new_db:
        new_db = database

    logger.info(f"Creating database {new_db} in destination if not exists")
    dest_client.create_database_if_not_exists(new_db)

    tables = source_client.list_tables()

    if dry_run:
        perform_dry_run_analysis(
            source_db=database,
            dest_db=new_db,
            tables=tables,
            dest_client=dest_client,
            table_exists_action=table_exists_action,
            source_endpoint=source_endpoint,
            dest_endpoint=dest_endpoint,
        )
        return

    if progress:
        print(f"Starting clone operation: {len(tables)} tables to process")
        table_progress = tqdm(total=len(tables), desc="Tables", unit="table")
    else:
        table_progress = None

    with ThreadPoolExecutor(max_workers=table_parallelism) as executor:
        for t in tables:
            executor.submit(
                copy_table,
                src_db=database,
                dest_db=new_db,
                tbl_name=t.name,
                src_client=source_client,
                dest_client=dest_client,
                writer=writer,
                table_exists_action=table_exists_action,
                download_parallelism=download_parallelism,
                chunk_size=chunk_size,
                table_progress=table_progress,
            )

    if table_progress:
        table_progress.close()

    logger.warning(f"Complete clone DB {database}")


def validate_source_database(client: pytd.Client, database: str) -> bool:  # type: ignore[name-defined]
    """Validate that the source database exists.

    Args:
        client: Source pytd.Client
        database: Database name to validate

    Returns:
        True if database exists, False otherwise
    """
    return client.exists(database)


def perform_dry_run_analysis(
    source_db: str,
    dest_db: str,
    tables: list,
    dest_client: pytd.Client,  # type: ignore[name-defined]
    table_exists_action: TableExistsAction,
    source_endpoint: str,
    dest_endpoint: str,
) -> None:
    """Perform dry-run analysis and display what would be done.

    Args:
        source_db: Source database name
        dest_db: Destination database name
        tables: List of source tables
        dest_client: Destination client
        table_exists_action: Action for existing tables
        source_endpoint: Source endpoint URL
        dest_endpoint: Destination endpoint URL
    """
    typer.echo("🔍 DRY RUN: Analyzing clone operation...")
    typer.echo(f"📊 Source: {source_db} ({source_endpoint})")
    typer.echo(f"📋 Destination: {dest_db} ({dest_endpoint})")
    typer.echo()

    # Analyze each table
    create_count = 0
    skip_count = 0
    overwrite_count = 0
    error_count = 0
    total_rows = 0

    typer.echo("📑 Tables to be processed:")
    for table in tables:
        exists = dest_client.exists(dest_db, table.name)

        # Get row count if available (might be None for newly created tables)
        row_count = table.count if table.count is not None else 0
        row_info = f"({row_count:,} rows)" if row_count > 0 else "(row count unknown)"

        if exists:
            if table_exists_action == TableExistsAction.SKIP:
                typer.echo(f"  ⚠️  {table.name} {row_info} → SKIP (already exists)")
                skip_count += 1
            elif table_exists_action == TableExistsAction.OVERWRITE:
                typer.echo(f"  🔥 {table.name} {row_info} → OVERWRITE (data loss possible)")
                overwrite_count += 1
                total_rows += row_count
            else:  # ERROR
                typer.echo(f"  ❌ {table.name} {row_info} → ERROR (already exists, will fail)")
                error_count += 1
        else:
            typer.echo(f"  ✅ {table.name} {row_info} → CREATE")
            create_count += 1
            total_rows += row_count

    typer.echo()
    typer.echo("📈 Summary:")
    typer.echo(f"  Total tables: {len(tables)}")
    typer.echo(f"  Will create: {create_count}")
    typer.echo(f"  Will skip: {skip_count}")
    typer.echo(f"  Will overwrite: {overwrite_count}")
    if error_count > 0:
        typer.echo(f"  Will error: {error_count}")

    if total_rows > 0:
        typer.echo(f"  Estimated rows to process: {total_rows:,}")

    # Show warnings
    warnings = []
    if overwrite_count > 0:
        warnings.append(f"⚠️  {overwrite_count} table(s) will be OVERWRITTEN (data loss possible)")
    if error_count > 0:
        warnings.append(f"❌ {error_count} table(s) will cause ERRORS due to existing data")

    if warnings:
        typer.echo()
        typer.echo("⚠️  Warnings:")
        for warning in warnings:
            typer.echo(f"  {warning}")

    typer.echo()
    if error_count > 0:
        typer.echo("💡 To proceed with existing tables, use --skip-existing or --overwrite")
    typer.echo("💡 To execute this operation, run the same command without --dry-run")


def copy_table(
    src_db: str,
    dest_db: str,
    tbl_name: str,
    src_client: pytd.Client,  # type: ignore[name-defined]
    dest_client: pytd.Client,  # type: ignore[name-defined]
    writer: pytd.writer.Writer,  # type: ignore[name-defined]
    table_exists_action: TableExistsAction = TableExistsAction.ERROR,
    download_parallelism: int = 4,
    chunk_size: int = 100_000,
    table_progress: tqdm | None = None,
):
    """Copy a single table from source to destination.

    Args:
        src_db: Source database name
        dest_db: Destination database name
        tbl_name: Table name to copy
        src_client: Source pytd.Client
        dest_client: Destination pytd.Client
        writer: pytd.writer.Writer instance
        table_exists_action: Action to take when table already exists
        download_parallelism: Number of parallel download threads
        chunk_size: Number of rows to process in each chunk
        table_progress: tqdm progress bar for tables (optional)
    """
    src = f"{src_db}.{tbl_name}"
    dest = f"{dest_db}.{tbl_name}"

    if table_progress:
        table_progress.set_description(f"Processing {tbl_name}")

    table_exists = dest_client.exists(dest_db, tbl_name)

    if table_exists:
        if table_exists_action == TableExistsAction.SKIP:
            logger.warning(f"{dest} already exists. Skipping as requested")
            if table_progress:
                table_progress.update(1)
            return
        elif table_exists_action == TableExistsAction.ERROR:
            logger.warning(f"{dest} already exists. Skip copying")
            if table_progress:
                table_progress.update(1)
            return
        # For OVERWRITE, we continue with the operation

    logger.warning(f"Start writing from {src} to {dest}")

    try:
        td_client = tdclient.Client(apikey=src_client.apikey, endpoint=src_client.endpoint, retry_post_requests=True)
        job = td_client.query(src_db, f"SELECT * FROM {src_db}.{tbl_name}", type="presto")
        job.wait()

        if not job.success():
            debug_info = job.debug.get("stderr", "Unknown error") if job.debug else "Unknown error"
            logger.error(f"Query job failed for table {src}: {debug_info}")
            raise Exception(f"Query failed for table {src}")

        logger.info(f"Query completed for {src}, starting chunked data processing")

        # Process data in chunks using parallel download
        _process_table_chunks(
            job=job,
            dest_client=dest_client,
            dest_db=dest_db,
            tbl_name=tbl_name,
            writer=writer,
            table_exists_action=table_exists_action,
            download_parallelism=download_parallelism,
            chunk_size=chunk_size,
            show_chunk_progress=table_progress is not None,
        )

        logger.warning(f"Finish writing to {dest}")

        if table_progress:
            table_progress.update(1)

    except tdclient.errors.AuthError as e:
        logger.error(
            f"Authentication failed for destination table {dest}. "
            "Please verify your API key and destination endpoint configuration. "
            f"Error: {e}"
        )
        raise
    except tdclient.errors.ForbiddenError as e:
        logger.error(
            f"Access forbidden for destination table {dest}. "
            "Please verify your API key has write permissions to the destination database. "
            f"Error: {e}"
        )
        raise
    except tdclient.errors.NotFoundError as e:
        logger.error(f"Destination database not found: {dest}. Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to copy table {src} to {dest}: {e}")
        raise


def _process_table_chunks(
    job: tdclient.models.Job,  # type: ignore[name-defined]
    dest_client: pytd.Client,  # type: ignore[name-defined]
    dest_db: str,
    tbl_name: str,
    writer: pytd.writer.Writer,  # type: ignore[name-defined]
    table_exists_action: TableExistsAction,
    download_parallelism: int,
    chunk_size: int,
    show_chunk_progress: bool = False,
) -> None:
    """Process table data in chunks using parallel download."""
    # Get column names from schema
    columns = [s[0] for s in job.result_schema]
    logger.info(f"Table schema: {columns}")

    # Get data iterator with parallel download
    data_iter = job.result_format("msgpack", store_tmpfile=True, num_threads=download_parallelism)

    dest = f"{dest_db}.{tbl_name}"
    table = pytd.table.Table(dest_client, dest_db, tbl_name)  # type: ignore[attr-defined]
    if_exists_param = "overwrite" if table_exists_action == TableExistsAction.OVERWRITE else "error"

    # Process data in chunks to avoid memory issues
    chunk_data = []
    total_rows = 0
    chunk_count = 0

    for row in data_iter:
        chunk_data.append(row)

        if len(chunk_data) >= chunk_size:
            _write_chunk_to_destination(
                chunk_data,
                columns,
                table,
                writer,
                if_exists_param if chunk_count == 0 else "append",
                download_parallelism,
            )
            total_rows += len(chunk_data)
            chunk_count += 1

            # Progress reporting
            if show_chunk_progress and chunk_count % 10 == 0:  # Report every 10 chunks
                print(f"  {tbl_name}: Processed {total_rows:,} rows ({chunk_count} chunks)")
            elif chunk_count % 10 == 0:  # Fallback to log progress every 10 chunks
                logger.info(f"Processed {total_rows} rows for {dest}")

            chunk_data = []

    # Write remaining data
    if chunk_data:
        _write_chunk_to_destination(
            chunk_data,
            columns,
            table,
            writer,
            if_exists_param if chunk_count == 0 else "append",
            download_parallelism,
        )
        total_rows += len(chunk_data)

    logger.info(f"Completed processing {total_rows} total rows for {dest}")


def _write_chunk_to_destination(
    chunk_data: list[Any],
    columns: list[str],
    table: pytd.table.Table,  # type: ignore[name-defined]
    writer: pytd.writer.Writer,  # type: ignore[name-defined]
    if_exists: str,
    max_workers: int = 4,
) -> None:
    """Write a chunk of data to the destination table."""
    # Create DataFrame for this chunk
    chunk_df = pd.DataFrame(chunk_data, columns=columns)  # type: ignore[arg-type]

    # Write chunk to destination
    writer.write_dataframe(chunk_df, table, if_exists=if_exists, fmt="msgpack", max_workers=max_workers)

    # Clean up
    del chunk_df
