"""Export Treasure Data query results to Parquet format."""

import logging
import os
from enum import Enum
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import tdclient
import typer
from tqdm.auto import tqdm

logger = logging.getLogger(__name__)


class Site(str, Enum):
    """Treasure Data site options."""

    aws = "aws"
    aws_tokyo = "aws-tokyo"
    eu01 = "eu01"
    ap02 = "ap02"
    ap03 = "ap03"


def get_api_endpoint(endpoint: str = None, site: str = "aws") -> str:
    """Get API endpoint based on endpoint or site."""
    if endpoint:
        return endpoint

    # Fallback to site-based endpoint
    site_endpoints = {
        "aws": "https://api.treasuredata.com",
        "aws-tokyo": "https://api.treasuredata.co.jp",
        "eu01": "https://api.eu01.treasuredata.com",
        "ap02": "https://api.ap02.treasuredata.com",
        "ap03": "https://api.ap03.treasuredata.com",
    }
    return site_endpoints.get(site, "https://api.treasuredata.com")


def save_as_parquet(df: pd.DataFrame, output_path: Path) -> None:
    """Save a DataFrame as a Parquet file."""
    df.to_parquet(output_path, index=False)
    logger.info(f"DataFrame saved as Parquet at {output_path}")


def save_incremental_parquet(job: tdclient.models.Job, output_path: Path, chunk_size: int = 10000) -> None:
    """Save query results incrementally to a Parquet file to avoid memory issues."""
    logger.info(f"Starting incremental save to {output_path}")

    # Get column names from schema
    columns = [s[0] for s in job.result_schema]
    logger.info(f"Schema: {columns}")

    # Get data iterator
    data_iter = job.result_format("msgpack", store_tmpfile=True, num_threads=4)

    writer = None
    table_schema = None
    total_rows = 0

    try:
        # Process data in chunks
        chunk_data = []
        for row in tqdm(data_iter, desc="Processing rows", unit="row"):
            chunk_data.append(row)

            if len(chunk_data) >= chunk_size:
                # Create DataFrame for this chunk
                chunk_df = pd.DataFrame(chunk_data, columns=columns)

                # Convert to Arrow table
                table = pa.Table.from_pandas(chunk_df)

                # Initialize writer with schema from first chunk
                if writer is None:
                    table_schema = table.schema
                    writer = pq.ParquetWriter(output_path, table_schema)
                    logger.info("Initialized Parquet writer with schema")

                # Write chunk to file
                writer.write_table(table)
                total_rows += len(chunk_data)

                # Clear chunk data
                chunk_data = []

        # Write remaining data
        if chunk_data:
            chunk_df = pd.DataFrame(chunk_data, columns=columns)
            table = pa.Table.from_pandas(chunk_df)

            if writer is None:
                table_schema = table.schema
                writer = pq.ParquetWriter(output_path, table_schema)
                logger.info("Initialized Parquet writer with schema")

            writer.write_table(table)
            total_rows += len(chunk_data)

    finally:
        if writer:
            writer.close()
            logger.info(f"Parquet file saved successfully: {total_rows} total rows written to {output_path}")


def fetch_table(db_name: str, table_name: str, endpoint: str = None, site: str = "aws") -> pd.DataFrame:
    """Fetch a table from the database."""
    api_endpoint = get_api_endpoint(endpoint, site)

    try:
        apikey = os.environ["TD_API_KEY"]
    except KeyError:
        typer.echo("Error: Missing TD_API_KEY environment variable", err=True)
        raise typer.Exit(2)

    client = tdclient.Client(apikey=apikey, endpoint=api_endpoint, retry_post_requests=True)

    try:
        logger.info(f"Fetching table {db_name}.{table_name} from {api_endpoint}")
        job = client.query(db_name, f"SELECT * FROM {db_name}.{table_name}", type="presto")
        job.wait()

        if job.success():
            logger.info("Job succeeded.")
            data = job.result_format("msgpack", store_tmpfile=True, num_threads=4)
            logger.info("Data fetched successfully.")
            return pd.DataFrame(data, columns=[s[0] for s in job.result_schema])
        else:
            logger.error(f"Job failed: {job.status()}")
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Error fetching table: {e}")
        raise typer.Exit(1)


def fetch_table_incremental(
    db_name: str,
    table_name: str,
    output_path: Path,
    endpoint: str = None,
    site: str = "aws",
    chunk_size: int = 10000,
) -> bool:
    """Fetch a table from the database and save incrementally to avoid memory issues."""
    api_endpoint = get_api_endpoint(endpoint, site)

    try:
        apikey = os.environ["TD_API_KEY"]
    except KeyError:
        typer.echo("Error: Missing TD_API_KEY environment variable", err=True)
        raise typer.Exit(2)

    client = tdclient.Client(apikey=apikey, endpoint=api_endpoint, retry_post_requests=True)

    try:
        logger.info(f"Fetching table {db_name}.{table_name} from {api_endpoint}")
        job = client.query(db_name, f"SELECT * FROM {db_name}.{table_name}", type="presto")
        job.wait()

        if job.success():
            logger.info("Job succeeded. Starting incremental save...")
            save_incremental_parquet(job, output_path, chunk_size)
            return True
        else:
            logger.error(f"Job failed: {job.status()}")
            return False

    except Exception as e:
        logger.error(f"Error fetching table: {e}")
        return False


def td2parquet_command(
    db_name: str = typer.Argument(..., help="Name of the database"),
    table_name: str = typer.Argument(..., help="Name of the table to export"),
    endpoint: str = typer.Option(
        None, "--endpoint", help="Treasure Data API endpoint URL (optional, takes precedence over site)"
    ),
    site: Site = typer.Option(Site.aws, "--site", help="Treasure Data site (used when endpoint not specified)"),
    output_dir: Path = typer.Option("dataset", "--output-dir", help="Output directory for Parquet files"),
    chunk_size: int = typer.Option(10000, "--chunk-size", help="Number of rows to process at a time"),
    use_incremental: bool = typer.Option(
        True,
        "--use-incremental/--no-use-incremental",
        help="Use incremental processing",
    ),
):
    """Export Treasure Data query results or tables to Parquet format.

    Environment Variables:
        TD_API_KEY: Treasure Data API key
    """
    if not output_dir.exists():
        logger.info(f"Creating output directory at {output_dir}")
        output_dir.mkdir(parents=True)

    output_path = output_dir / f"{db_name}_{table_name}.parquet"

    if use_incremental:
        logger.info(f"Using incremental processing with chunk size: {chunk_size}")
        success = fetch_table_incremental(db_name, table_name, output_path, endpoint, site.value, chunk_size)
        if success:
            logger.info(f"Data successfully saved to {output_path}")
        else:
            logger.error("Failed to fetch and save data")
            raise typer.Exit(1)
    else:
        logger.info("Using legacy method (loads all data into memory)")
        df = fetch_table(db_name, table_name, endpoint, site.value)
        if not df.empty:
            logger.info(f"Saving DataFrame to {output_dir}")
            save_as_parquet(df, output_path)
            logger.info(f"DataFrame saved as Parquet at {output_path}")
        else:
            logger.error("No data fetched or error occurred")
            raise typer.Exit(1)
