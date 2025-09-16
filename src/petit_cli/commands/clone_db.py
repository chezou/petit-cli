"""Clone/copy databases between Treasure Data instances."""

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

import pandas as pd
import pytd
import tdclient
import tdclient.errors
import typer

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
):
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

    source_client = pytd.Client(database=database, apikey=source_api_key, endpoint=source_endpoint)
    dest_client = pytd.Client(apikey=dest_api_key, endpoint=dest_endpoint)

    if not validate_source_database(source_client, database):
        typer.echo(
            "Error: Source database does not exist or access denied. "
            "Please verify your API key and source endpoint configuration.",
            err=True,
        )
        raise typer.Exit(2)

    writer = pytd.writer.BulkImportWriter()

    if not new_db:
        new_db = database

    logger.info(f"Creating database {new_db} in destination if not exists")
    dest_client.create_database_if_not_exists(new_db)

    with ThreadPoolExecutor(max_workers=table_parallelism) as executor:
        for t in source_client.list_tables():
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
            )

    logger.warning(f"Complete clone DB {database}")


def validate_source_database(client: pytd.Client, database: str) -> bool:
    """Validate that the source database exists.

    Args:
        client: Source pytd.Client
        database: Database name to validate

    Returns:
        True if database exists, False otherwise
    """
    return client.exists(database)


def copy_table(
    src_db: str,
    dest_db: str,
    tbl_name: str,
    src_client: pytd.Client,
    dest_client: pytd.Client,
    writer: pytd.writer.Writer,
    table_exists_action: TableExistsAction = TableExistsAction.ERROR,
    download_parallelism: int = 4,
    chunk_size: int = 100_000,
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
    """
    src = f"{src_db}.{tbl_name}"
    dest = f"{dest_db}.{tbl_name}"

    table_exists = dest_client.exists(dest_db, tbl_name)

    if table_exists:
        if table_exists_action == TableExistsAction.SKIP:
            logger.warning(f"{dest} already exists. Skipping as requested")
            return
        elif table_exists_action == TableExistsAction.ERROR:
            logger.warning(f"{dest} already exists. Skip copying")
            return
        # For OVERWRITE, we continue with the operation

    logger.warning(f"Start writing from {src} to {dest}")

    try:
        td_client = tdclient.Client(apikey=src_client.apikey, endpoint=src_client.endpoint, retry_post_requests=True)
        job = td_client.query(src_db, f"SELECT * FROM {src_db}.{tbl_name}", type="presto")
        job.wait()

        if not job.success():
            logger.error(f"Query job failed for table {src}: {job.debug['stderr']}")
            raise Exception(f"Query failed for table {src}")

        logger.info(f"Query completed for {src}, starting chunked data processing")

        # Process data in chunks using parallel download
        _process_table_chunks(
            job, dest_client, dest_db, tbl_name, writer, table_exists_action, download_parallelism, chunk_size
        )

        logger.warning(f"Finish writing to {dest}")

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
    job: tdclient.models.Job,
    dest_client: pytd.Client,
    dest_db: str,
    tbl_name: str,
    writer: pytd.writer.Writer,
    table_exists_action: TableExistsAction,
    download_parallelism: int,
    chunk_size: int,
) -> None:
    """Process table data in chunks using parallel download."""
    # Get column names from schema
    columns = [s[0] for s in job.result_schema]
    logger.info(f"Table schema: {columns}")

    # Get data iterator with parallel download
    data_iter = job.result_format("msgpack", store_tmpfile=True, num_threads=download_parallelism)

    dest = f"{dest_db}.{tbl_name}"
    table = pytd.table.Table(dest_client, dest_db, tbl_name)
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

            if chunk_count % 10 == 0:  # Log progress every 10 chunks
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
    chunk_data: list,
    columns: list[str],
    table: pytd.table.Table,
    writer: pytd.writer.Writer,
    if_exists: str,
    max_workers: int = 4,
) -> None:
    """Write a chunk of data to the destination table."""
    # Create DataFrame for this chunk
    chunk_df = pd.DataFrame(chunk_data, columns=columns)

    # Write chunk to destination
    writer.write_dataframe(chunk_df, table, if_exists=if_exists, fmt="msgpack", max_workers=max_workers)

    # Clean up
    del chunk_df
