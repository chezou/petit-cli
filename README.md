# Petit CLI

Tiny tools for Treasure Data operations - A unified CLI for common TD data management tasks.

## Overview

Petit CLI provides convenient command-line tools for working with Treasure Data:

- **td2parquet**: Export TD tables to Parquet format with incremental processing
- **clone-db**: Clone/copy entire databases between TD instances

## Installation

### Using uvx (Recommended)

Clone the repository and run using uvx:

```bash
# Show help
uvx --from git+https://github.com/chezou/petit-cli petit-cli --help

# Export table to Parquet
TD_API_KEY=your_api_key uvx --from git+https://github.com/chezou/petit-cli petit-cli td2parquet your_database your_table

# Clone database
SOURCE_API_KEY=src_key DEST_API_KEY=dest_key uvx --from git+https://github.com/chezou/petit-cli petit-cli clone-db source_db --new-db destination_db
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/chezou/petit-cli
cd petit-cli

# Run commands directly with uv
uv run petit-cli --help
```

## Commands

### td2parquet

Export Treasure Data tables to Parquet format with support for large datasets through incremental processing.

#### Usage

```bash
TD_API_KEY=your_api_key petit-cli td2parquet [OPTIONS] DATABASE TABLE
```

#### Arguments

- `DATABASE`: Name of the source database
- `TABLE`: Name of the table to export

#### Options

- `--endpoint TEXT`: Custom TD endpoint URL (overrides site selection)
- `--site [aws|aws-tokyo|eu01|ap02|ap03]`: TD site selection (default: aws)
- `--output-dir PATH`: Output directory for Parquet files (default: current directory)
- `--chunk-size INTEGER`: Number of rows to process per chunk (default: 100000)
- `--time-column TEXT`: Column name for time-based partitioning
- `--start-time TEXT`: Start time for data export (ISO format)
- `--end-time TEXT`: End time for data export (ISO format)
- `--use-incremental/--no-use-incremental`: Enable incremental processing (default: enabled)
- `--help`: Show help message

#### Examples

```bash
# Basic export (uses aws site by default)
TD_API_KEY=your_key petit-cli td2parquet my_database my_table

# Export using eu01 site
TD_API_KEY=your_key petit-cli td2parquet my_database my_table --site eu01

# Export with custom endpoint
TD_API_KEY=your_key petit-cli td2parquet my_database my_table \
  --endpoint https://api-ap02.treasuredata.com

# Export with time range
TD_API_KEY=your_key petit-cli td2parquet my_database my_table \
  --time-column created_at \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z"

# Custom output directory and chunk size
TD_API_KEY=your_key petit-cli td2parquet my_database my_table \
  --output-dir ./exports \
  --chunk-size 50000
```

### clone-db

Clone/copy entire databases between Treasure Data instances with parallel table processing.

#### Usage

```bash
SOURCE_API_KEY=src_key DEST_API_KEY=dest_key petit-cli clone-db [OPTIONS] DATABASE
```

#### Arguments

- `DATABASE`: Name of the source database to clone

#### Options

- `--se, --source-endpoint TEXT`: Source TD endpoint URL (default: https://api.treasuredata.com/)
- `--de, --dest-endpoint TEXT`: Destination TD endpoint URL (default: https://api.treasuredata.com/)
- `--new-db TEXT`: New database name in destination (default: same as source)
- `--skip-existing`: Skip tables that already exist in destination
- `--overwrite`: Overwrite existing tables in destination (cannot be used with --skip-existing)
- `--help`: Show help message

#### Examples

```bash
# Basic database cloning
SOURCE_API_KEY=key DEST_API_KEY=key petit-cli clone-db prod_data --new-db test_data

# Skip existing tables during cloning
SOURCE_API_KEY=key DEST_API_KEY=key petit-cli clone-db prod_data --new-db backup_data --skip-existing

# Overwrite existing tables during cloning
SOURCE_API_KEY=key DEST_API_KEY=key petit-cli clone-db prod_data --new-db backup_data --overwrite

# Clone between different TD instances
SOURCE_API_KEY=prod_key DEST_API_KEY=dev_key petit-cli clone-db marketing_data \
  --de https://api.treasuredata.co.jp \
  --new-db marketing_data_copy

# Clone to different region with overwrite option
SOURCE_API_KEY=us_key DEST_API_KEY=eu_key petit-cli clone-db user_data \
  --se https://api.treasuredata.com/ \
  --de https://api.eu01.treasuredata.com/ \
  --new-db user_data_eu \
  --overwrite
```

## Environment Variables

### Required for td2parquet

- `TD_API_KEY`: Your Treasure Data API key

### Required for clone-db

- `SOURCE_API_KEY`: API key for source Treasure Data instance
- `DEST_API_KEY`: API key for destination Treasure Data instance

## Features

### td2parquet Features

- **Incremental Processing**: Handles large datasets by processing in configurable chunks
- **Flexible Output**: Customizable output directory and file naming
- **Memory Efficient**: Streams data to avoid memory issues with large tables

### clone-db Features

- **Parallel Processing**: Copies multiple tables concurrently for faster cloning
- **Cross-instance Support**: Clone between different TD sites and accounts

## Performance Considerations

### td2parquet

- Use appropriate `--chunk-size` based on your data size and memory constraints
- Smaller chunks use less memory but may be slower for very large datasets
- Time-based filtering can significantly reduce processing time for large tables

### clone-db

- Currently uses 5 parallel workers for table copying
- Performance depends on table sizes and network connectivity
- Large tables may take significant time to copy

## Troubleshooting

### Common Issues

1. **API Key Authentication**:
   ```
   Error: Missing environment variable 'TD_API_KEY'
   ```
   Solution: Ensure your API key environment variables are properly set

2. **Network Timeouts**:
   ```
   Connection timeout to Treasure Data endpoint
   ```
   Solution: Check network connectivity and endpoint URLs

3. **Insufficient Permissions**:
   ```
   Access denied to database/table
   ```

   Solution: Verify your API key has appropriate read/write permissions

4. **Memory Issues with Large Datasets**:
   ```
   MemoryError: Unable to allocate memory
   ```
   Solution: Reduce `--chunk-size` or use time-based filtering

### Debug Mode

Enable debug logging by setting the environment variable:

```bash
export PYTHONPATH=src
export LOG_LEVEL=DEBUG
```

## Contributing

This project uses modern Python tooling:

- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Testing**: pytest with comprehensive unit tests
- **Code Quality**: ruff for formatting and linting
- **CLI Framework**: Typer for type-safe command interfaces

### Development Setup

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run ruff format

# Lint code
uv run ruff check
```

### Running Tests

```bash
# Unit tests
uv run pytest
```

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

## Version

Current version: 0.0.1

Use `petit-cli --version` to check the installed version.
