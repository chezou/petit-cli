# Petit CLI - Requirements Document

## Overview

Petit CLI is a collection of Python-based command-line tools for Treasure Data operations, designed to be installed and executed using `uvx` from a Git repository subdirectory.

## Project Goals

The primary goal is to consolidate multiple standalone Python tools into a unified package that can be easily distributed and executed via:

```bash
uvx --from git+https://github.com/chezou/petit-cli.git petit-cli <command-name>
```

## Command Requirements

### 1. clone-db Command

**Purpose**: Clone/copy databases between Treasure Data instances

**Source**: `src/clone_db.py`

**Current Implementation**: Uses Click framework

**Migration Requirements**:

- Convert from Click to Typer framework
- Maintain all existing functionality:
  - Source endpoint configuration (`--se`)
  - Destination endpoint configuration (`--de`)
  - Optional new database name (`--new-db`)
  - Database argument (positional)
- Preserve environment variable requirements:
  - `SOURCE_API_KEY`: API key for source TD instance
  - `DEST_API_KEY`: API key for destination TD instance
- Maintain concurrent table copying functionality
- Keep all validation logic (API key validation, etc.)

### 2. td2parquet Command

**Purpose**: Export Treasure Data query results to Parquet format

**Source**: `src/td2parquet.py`

**Current Implementation**: Already uses Typer framework

**Migration Requirements**:

- Integrate existing Typer-based functionality
- Maintain all current features:
  - Incremental export to handle large datasets
  - Configurable chunk size for memory management
  - Progress indication with tqdm
  - Schema detection and preservation
- Preserve all command-line options and arguments

## Technical Requirements

### Package Structure

```text
petit-cli/
├── pyproject.toml          # Package configuration
├── README.md              # Package documentation
├── docs/
│   └── requirements.md    # This document
├── src/
│   ├── __init__.py        # Package initialization
│   ├── main.py           # CLI entry point with Typer app
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── clone_db.py   # clone-db command implementation
│   │   └── td2parquet.py # td2parquet command implementation
│   └── utils/            # Shared utilities (if needed)
```

### Dependencies

**Core Framework**:

- Typer: Modern CLI framework with type hints support
- Python >= 3.11

**Data Processing**:

- pandas: Data manipulation
- pyarrow: Parquet file format support
- pytd: Treasure Data client library
- td-client: Alternative TD client for specific operations
- tqdm: Progress bars

### CLI Common Requirements

**Version Information**:

- `--version` option must be available on main CLI entry point
- Version information must be read dynamically from `pyproject.toml`
- Should display format: `petit-cli X.Y.Z`

### Entry Points Configuration

The package must define console script entry points in `pyproject.toml`:

```toml
[project.scripts]
clone-db = "petit_cli.main:clone_db_command"
td2parquet = "petit_cli.main:td2parquet_command"
```

### uvx Compatibility

The package must be compatible with `uvx` installation from Git repositories with subdirectory specification:

1. **Git Repository Structure**: Must work from subdirectory `aki/petit-cli`
2. **Dependency Resolution**: All dependencies must be properly declared in `pyproject.toml`
3. **Entry Points**: Commands must be executable immediately after installation
4. **No Build Dependencies**: Should work with standard Python packaging tools

## Non-Functional Requirements

### Performance

- Maintain concurrent processing capabilities for database cloning
- Support incremental processing for large Parquet exports
- Minimal memory footprint for large datasets

### Reliability

- Proper error handling and user feedback
- Graceful handling of network interruptions
- Data integrity validation

### Usability

- Consistent help messages and option naming
- Clear progress indication for long-running operations
- Intuitive command structure following CLI best practices
