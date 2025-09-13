"""Clone/copy databases between Treasure Data instances."""

import logging
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import pytd
import typer

logger = logging.getLogger(__name__)
logging.getLogger("pytd.query_engine").setLevel(logging.ERROR)


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
):
    """Clone/copy databases between Treasure Data instances.

    Environment Variables:
        SOURCE_API_KEY: API key for source Treasure Data instance
        DEST_API_KEY: API key for destination Treasure Data instance
    """
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
    writer = pytd.writer.BulkImportWriter()

    if not new_db:
        new_db = database

    logger.info(f"Creating database {new_db} in destination if not exists")
    dest_client.create_database_if_not_exists(new_db)

    with ThreadPoolExecutor(max_workers=5) as executor:
        for t in source_client.list_tables():
            executor.submit(
                copy_table,
                src_db=database,
                dest_db=new_db,
                tbl_name=t.name,
                src_client=source_client,
                dest_client=dest_client,
                writer=writer,
            )

    logger.warning(f"Complete clone DB {database}")


def copy_table(
    src_db: str,
    dest_db: str,
    tbl_name: str,
    src_client: pytd.Client,
    dest_client: pytd.Client,
    writer: pytd.writer.Writer,
):
    """Copy a single table from source to destination."""
    src = f"{src_db}.{tbl_name}"
    dest = f"{dest_db}.{tbl_name}"
    if dest_client.exists(dest_db, tbl_name):
        logger.warning(f"{dest} already exists. Skip copying")
        return
    logger.warning(f"Start writing from {src} to {dest}")
    # To avoid api-presto hostname issue on dev, use `force_tdclient`
    df = pd.DataFrame(**src_client.query(f"select * from {src}", force_tdclient=True))
    table = pytd.table.Table(dest_client, dest_db, tbl_name)
    writer.write_dataframe(df, table, if_exists="error", fmt="msgpack")

    del df
    logger.warning(f"Finish writing to {dest}")
