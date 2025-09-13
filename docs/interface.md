# Petit CLI - Command Line Interface Specification

## Overview

This document defines the command-line interface for Petit CLI tools, designed to be executed via `uvx` from a Git repository.

## Installation and Execution

### Installation Method

```bash
# Install and run commands directly with uvx
uvx --from git+https://github.com/chezou/petit-cli petit-cli <command-name> [options]
```

## Commands

### 1. clone-db Command

**Purpose**: Clone/copy databases between Treasure Data instances

#### Usage

```bash
uvx --from git+https://github.com/chezou/petit-cli petit-cli clone-db [OPTIONS] DATABASE
```

#### Arguments

- `DATABASE` (required): Name of the source database to clone

#### Options

- `--se, --source-endpoint TEXT`: Source Treasure Data endpoint URL  
  Default: `https://api.treasuredata.com/`
- `--de, --dest-endpoint TEXT`: Destination Treasure Data endpoint URL  
  Default: `https://api.treasuredata.com/`
- `--new-db TEXT`: New database name in destination  
  Default: Same as source database name
- `--help`: Show help message and exit

#### Environment Variables

- `SOURCE_API_KEY` (required): API key for source Treasure Data instance
- `DEST_API_KEY` (required): API key for destination Treasure Data instance

#### Examples

```bash
# Basic database cloning (same endpoint, different credentials)
export SOURCE_API_KEY="source-api-key-here"
export DEST_API_KEY="dest-api-key-here"
uvx --from git+https://github.com/chezou/petit-cli clone-db my_database

# Clone database with custom name
uvx --from git+https://github.com/chezou/petit-cli clone-db my_database --new-db my_database_backup

# Clone between different Treasure Data instances
uvx --from git+https://github.com/chezou/petit-cli clone-db my_database \
  --se https://api.treasuredata.com/ \
  --de https://api.treasuredata.co.jp/ \
  --new-db migrated_database

# Get help
uvx --from git+https://github.com/chezou/petit-cli clone-db --help
```

### 2. td2parquet Command

**Purpose**: Export Treasure Data query results or tables to Parquet format

#### Usage

```bash
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet [OPTIONS] DB_NAME TABLE_NAME
```

#### Arguments

- `DB_NAME` (required): Name of the database
- `TABLE_NAME` (required): Name of the table to export

#### Options

- `--endpoint TEXT`: Custom Treasure Data endpoint URL (overrides site selection)
- `--site TEXT`: Treasure Data site  
  Choices: `aws`, `aws-tokyo`, `eu01`, `ap02`, `ap03`  
  Default: `aws`
- `--output-dir PATH`: Output directory for Parquet files  
  Default: `dataset`
- `--chunk-size INTEGER`: Number of rows to process at a time  
  Default: `10000`
- `--time-column TEXT`: Column name for time-based partitioning
- `--start-time TEXT`: Start time for data export (ISO format)
- `--end-time TEXT`: End time for data export (ISO format)
- `--use-incremental/--no-use-incremental`: Use incremental processing  
  Default: `--use-incremental`
- `--help`: Show help message and exit

#### Environment Variables

- `TD_API_KEY` (required): Treasure Data API key

#### Examples

```bash
# Basic table export
export TD_API_KEY="your-td-api-key-here"
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet my_db my_table

# Export with custom output directory
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet my_db my_table --output-dir /path/to/output

# Export from Tokyo site
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet my_db my_table --site aws-tokyo

# Export with custom endpoint
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet my_db my_table --endpoint https://api-ap02.treasuredata.com

# Export with time range filtering
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet my_db my_table \
  --time-column created_at \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z"

# Export with custom chunk size for large tables
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet my_db my_table --chunk-size 50000

# Disable incremental processing (load all data into memory)
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet my_db my_table --no-use-incremental

# Export from EU region with custom settings
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet my_db my_table \
  --site eu01 \
  --stage production \
  --output-dir ./exports \
  --chunk-size 25000

# Get help
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet --help
```

## Common Usage Patterns

### Development Workflow

```bash
# Set up environment variables
export TD_API_KEY="your-api-key"
export SOURCE_API_KEY="source-api-key"
export DEST_API_KEY="dest-api-key"

# Export data for analysis
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet analytics_db user_events --output-dir ./data

# Clone database for testing
uvx --from git+https://github.com/chezou/petit-cli petit-cli clone-db production_db --new-db test_db

# Export from different environments
uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet staging_db events --stage staging --output-dir ./staging_data
```

### Batch Operations

```bash
# Export multiple tables (using shell loop)
for table in users events transactions; do
  uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet my_db $table --output-dir ./exports
done

# Clone multiple databases
for db in db1 db2 db3; do
  uvx --from git+https://github.com/chezou/petit-cli petit-cli clone-db $db --new-db "${db}_backup"
done
```

## Interface Consistency

### Common Patterns

- All commands use lowercase with hyphens (kebab-case): `clone-db`, `td2parquet`
- Help is always available via `--help`
- Version information is available via `--version` (reads from pyproject.toml)
- Environment variables follow TD conventions: `TD_API_KEY`, `SOURCE_API_KEY`, `DEST_API_KEY`
- Default values are sensible for production use
- Progress indication is provided for long-running operations
- Error messages are clear and actionable

### Output Format

- `clone-db`: Logs progress to stderr, no stdout output unless error
- `td2parquet`: Progress bars and status messages to stderr, file output to specified directory

### Exit Codes

- `0`: Success
- `1`: General error (invalid arguments, API errors, etc.)
- `2`: Environment error (missing API keys, invalid endpoints, etc.)
