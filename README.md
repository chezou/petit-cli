# Petit CLI

[![CI](https://github.com/chezou/petit-cli/workflows/CI/badge.svg)](https://github.com/chezou/petit-cli/actions/workflows/ci.yml)

Tiny tools for Treasure Data operations - A unified CLI for common TD data management tasks.

## 🌟 New Features (v0.1.0)

- **🔍 Dry-run Mode**: Preview operations before execution with detailed analysis
- **📊 Progress Reporting**: Real-time progress bars with ETA for long-running operations  
- **⚡ Performance Optimization**: Configurable parallel processing for large datasets
- **🛡️ Enhanced Error Handling**: Clear validation and user-friendly error messages
- **🔒 Type Safety**: Complete type checking with pyright for robust code quality

## Overview

Petit CLI provides convenient command-line tools for working with Treasure Data:

- **td2parquet**: Export TD tables to Parquet format with incremental processing
- **clone-db**: Clone/copy entire databases between TD instances with advanced options

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

**Basic Options**:
- `--se, --source-endpoint TEXT`: Source TD endpoint URL (default: <https://api.treasuredata.com/>)
- `--de, --dest-endpoint TEXT`: Destination TD endpoint URL (default: <https://api.treasuredata.com/>)
- `--new-db TEXT`: New database name in destination (default: same as source)

**Table Handling** (mutually exclusive):
- `--skip-existing`: Skip tables that already exist in destination
- `--overwrite`: Overwrite existing tables in destination

**Advanced Options**:
- `--dry-run`: Preview operations without execution (shows what would be created/skipped/overwritten)
- `--progress / --no-progress`: Show/hide progress bars (default: enabled)
- `--table-parallelism INTEGER`: Number of tables to process concurrently (default: 2)
- `--download-parallelism INTEGER`: Parallel downloads per table (default: 4)
- `--chunk-size INTEGER`: Rows per chunk for memory efficiency (default: 10000)

**Other**:
- `--help`: Show help message

#### Examples

**Basic Operations**:

```bash
# Preview operation before execution (recommended!)
SOURCE_API_KEY=key DEST_API_KEY=key petit-cli clone-db prod_data --new-db test_data --dry-run

# Basic database cloning with progress bars
SOURCE_API_KEY=key DEST_API_KEY=key petit-cli clone-db prod_data --new-db test_data

# Skip existing tables during cloning
SOURCE_API_KEY=key DEST_API_KEY=key petit-cli clone-db prod_data --new-db backup_data --skip-existing

# Overwrite existing tables with confirmation
SOURCE_API_KEY=key DEST_API_KEY=key petit-cli clone-db prod_data --new-db backup_data --overwrite
```

**Performance Optimization**:

```bash
# High-performance cloning for large databases
SOURCE_API_KEY=key DEST_API_KEY=key petit-cli clone-db large_db --new-db large_db_copy \
  --table-parallelism 4 \
  --download-parallelism 8 \
  --chunk-size 50000

# Memory-efficient cloning for resource-constrained environments
SOURCE_API_KEY=key DEST_API_KEY=key petit-cli clone-db huge_db --new-db huge_db_copy \
  --table-parallelism 1 \
  --download-parallelism 2 \
  --chunk-size 5000
```

**Cross-Region and Multi-Instance**:

```bash
# Clone between different TD instances
SOURCE_API_KEY=prod_key DEST_API_KEY=dev_key petit-cli clone-db marketing_data \
  --de https://api.treasuredata.co.jp \
  --new-db marketing_data_copy

# Clone to different region with performance tuning
SOURCE_API_KEY=us_key DEST_API_KEY=eu_key petit-cli clone-db user_data \
  --se https://api.treasuredata.com/ \
  --de https://api.eu01.treasuredata.com/ \
  --new-db user_data_eu \
  --overwrite \
  --table-parallelism 3 \
  --no-progress  # For automated scripts
```

## Environment Variables

### Required for td2parquet

- `TD_API_KEY`: Your Treasure Data API key

### Required for clone-db

- `SOURCE_API_KEY`: API key for source Treasure Data instance
- `DEST_API_KEY`: API key for destination Treasure Data instance

## 🚀 Best Practices

### clone-db Best Practices

1. **Always use dry-run first**: Preview operations before execution
   ```bash
   petit-cli clone-db my_database --new-db my_copy --dry-run
   ```

2. **Optimize for your data size**:
   - **Small databases** (< 100 tables): Use defaults
   - **Medium databases** (100-1000 tables): `--table-parallelism 4`
   - **Large databases** (1000+ tables): `--table-parallelism 2 --download-parallelism 8`

3. **Handle existing destinations**:
   - **Development**: Use `--skip-existing` to avoid conflicts
   - **Backup restore**: Use `--overwrite` with caution
   - **Never use both flags together**

4. **Monitor progress**: Keep `--progress` enabled for long operations (default)

5. **Memory optimization**: Reduce `--chunk-size` if encountering memory issues

### td2parquet Best Practices

1. **Use incremental processing** for large tables (enabled by default)
2. **Adjust chunk size** based on available memory and table size
3. **Choose appropriate sites** when working across regions

## Features

### 🔍 Advanced Operations

- **Dry-run Mode**: Preview all operations before execution with detailed analysis
- **Progress Reporting**: Real-time progress bars with ETA and completion tracking
- **Smart Error Handling**: Clear validation messages and user-friendly error guidance
- **Robust Retry Logic**: Built-in retry mechanisms for transient network failures

### 📊 Performance Features

- **Configurable Parallelism**: Tune table-level and download-level concurrency
- **Memory-Efficient Processing**: Chunked data streaming to handle large datasets
- **Optimized Transfers**: Parallel downloads with customizable chunk sizes
- **Resource Management**: Configurable resource usage for different environments

### 🛡️ Safety Features

- **Pre-execution Validation**: Source database and authentication checks
- **Conflict Resolution**: Skip existing tables or overwrite with warnings
- **Data Loss Prevention**: Clear warnings for destructive operations
- **Operation Logging**: Comprehensive logging for audit trails

### td2parquet Specific

- **Incremental Processing**: Handles large datasets by processing in configurable chunks
- **Flexible Output**: Customizable output directory and file naming
- **Multi-Site Support**: Compatible with all TD regions (AWS, Tokyo, EU, AP)

### clone-db Specific

- **Parallel Table Processing**: Concurrent table copying with progress tracking
- **Cross-Instance Support**: Clone between different TD sites and accounts
- **Flexible Destination Handling**: Skip, overwrite, or error on existing tables
- **Performance Tuning**: Configurable parallelism and chunk sizes

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
- **Testing**: pytest with comprehensive unit tests (86% coverage)
- **Code Quality**: ruff for formatting and linting + pyright for type checking
- **CLI Framework**: Typer for type-safe command interfaces
- **Progress Tracking**: tqdm for user-friendly progress bars

### Development Setup

```bash
# Clone repository
git clone https://github.com/chezou/petit-cli
cd petit-cli

# Install dependencies
uv sync --dev

# Run tests with coverage
uv run pytest --cov=petit_cli

# Code quality checks
uv run ruff format        # Format code
uv run ruff check         # Lint code  
uv run pyright           # Type checking

# All quality checks at once
uv run ruff format && uv run ruff check && uv run pyright && uv run pytest --cov=petit_cli
```

### Continuous Integration

Every pull request and push is automatically tested with:

- **Multi-Python support**: Tested on Python 3.11 and 3.12
- **Type safety**: Full pyright type checking with 0 errors
- **Code quality**: Ruff linting and formatting checks  
- **Test coverage**: 86% coverage with comprehensive test scenarios
- **Cross-platform**: Automated testing on Ubuntu (GitHub Actions)

See [.github/workflows/ci.yml](.github/workflows/ci.yml) for complete CI configuration.

### Running Tests

```bash
# Unit tests
uv run pytest
```

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

## Version

Current version: 0.1.0 (Milestone 2 - Enhanced UX & Reliability)

**What's New in v0.1.0**:

- 🔍 Dry-run mode for operation preview
- 📊 Real-time progress reporting with ETA
- ⚡ Configurable parallel processing
- 🛡️ Enhanced error handling and validation
- 🔒 Complete type safety with pyright
- 📈 86% test coverage with comprehensive scenarios

Use `petit-cli --version` to check the installed version.
