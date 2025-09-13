# AGENTS.md

## Project overview

Petit CLI is a collection of Python-based command-line tools for Treasure Data operations, designed to be installed and executed using `uvx` from a Git repository subdirectory.

**Installation method**: `uvx --from git+https://github.com/chezou/petit-cli petit-cli <command-name>`

**Commands**:
- `clone-db`: Clone/copy databases between Treasure Data instances
- `td2parquet`: Export Treasure Data query results to Parquet format

## Setup commands

```bash
# Install dependencies
uv sync

# Run commands locally for development
uv run python -m petit_cli.main <command> [options]

# Test uvx installation from Git
uvx --from git+https://github.com/chezou/petit-cli petit-cli <command> --help
```

## Build and test commands

```bash
# Run unit tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=petit_cli

# Lint code
uv run ruff check .
uv run ruff format --check .

# Fix linting issues
uv run ruff check --fix .
uv run ruff format .

# Type checking
uv run mypy petit_cli
```

## Code style guidelines

- Python >= 3.11 with type hints
- Use Typer for all CLI interfaces
- Follow PEP 8 naming conventions (snake_case for functions/variables, kebab-case for CLI commands)
- Use pathlib.Path for file operations
- Add comprehensive docstrings for all public functions
- Keep functions focused and testable

## Testing instructions

- Write unit tests for all new functionality using pytest
- Mock external dependencies (Treasure Data API calls) in tests
- Test CLI interfaces using Typer's testing utilities
- Aim for >80% test coverage
- Include integration tests for end-to-end workflows
- Test uvx installation and command execution

## Project structure

```
petit-cli/
├── AGENTS.md                    # This file
├── pyproject.toml              # Package configuration and dependencies
├── README.md                   # User documentation
├── docs/                       # Development documentation
│   ├── requirements.md         # Requirements specification
│   ├── plan.md                # Implementation plan with checkboxes
│   └── interface.md            # CLI interface specification
├── src/
│   ├── clone_db.py            # Original clone-db tool (Click-based)
│   └── td2parquet.py          # Original td2parquet tool (Typer-based)
└── tests/                     # Test files (to be created)
```

## Development workflow

1. **Read documentation first**: Always check `docs/requirements.md`, `docs/plan.md`, and `docs/interface.md`
2. **Update plan**: Mark checkboxes in `docs/plan.md` as tasks are completed
3. **Test incrementally**: Test each change before proceeding
4. **Maintain interface consistency**: Ensure implementation matches `docs/interface.md`

**Note on documentation versioning**: The documentation files (`requirements.md`, `interface.md`, `plan.md`) may be versioned or recreated for different phases of development. Particularly `plan.md` should not be reused across major phases - create new plan files organized by phase (e.g., `docs/phase1/plan.md`, `docs/phase2/plan.md`) to maintain clear progress tracking for each development cycle.

## Environment variables

Required for functionality:
- `TD_API_KEY`: Treasure Data API key (for td2parquet)
- `SOURCE_API_KEY`: Source TD instance API key (for clone-db)
- `DEST_API_KEY`: Destination TD instance API key (for clone-db)

## Current implementation status

Check `docs/plan.md` for detailed progress, or `docs/phase{N}/plan.md` for phase-specific plans. Key phases:
1. **Project Structure Setup** - Setting up proper Python package structure
2. **Command Migration** - Converting Click to Typer, adding unit tests
3. **Testing and Validation** - Comprehensive testing including uvx installation
4. **Documentation** - User guides and examples

## Security considerations

- Never commit API keys to version control
- Use environment variables for all credentials
- Validate all user inputs before processing
- Handle API rate limits gracefully
- Implement proper error handling for network failures

## Key files to understand

- `pyproject.toml`: Package configuration, needs entry points for console scripts
- `docs/interface.md`: Complete CLI specification that implementation must match

## Common pitfalls

- Don't modify the original tools until new structure is ready
- Ensure uvx compatibility by testing from Git repository
- Maintain backward compatibility for all existing functionality
- Test with real Treasure Data instances before finalizing
- Keep CLI interface consistent between commands
- Keep `__init__.py` files empty (no code should be added to them)

## Important reminders from development

- **Never destructively modify plan.md**: When implementation deviates from original plan, add "Additional Tasks" section instead of overwriting original tasks
- **Don't add features without requirements**: Never add functionality that isn't explicitly specified in docs/requirements.md or docs/interface.md - always ask for clarification first
- **Avoid redundant status indicators**: Use simple `[x]` checkboxes in markdown - don't add emojis like ✅ after checkboxes
- **Check file contents before editing**: Always read current file contents before making edits, especially after user interventions
- **Stick to documented requirements**: Phase 1 is about basic structure only - don't implement functionality that belongs to later phases
- **Avoid over-engineering error handling**: Don't add try-except blocks for scenarios that won't occur in actual usage patterns (uvx, uv run)
- **Always run code quality checks**: Execute `ruff format && ruff check --fix` before presenting any code changes to ensure consistent style and quality
