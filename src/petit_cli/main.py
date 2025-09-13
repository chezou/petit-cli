"""Main CLI entry point for petit-cli."""

import importlib.metadata

import typer

from .commands.clone_db import clone_db_command
from .commands.td2parquet import td2parquet_command

app = typer.Typer(
    name="petit-cli",
    help="Petit CLI - Collection of Treasure Data command-line tools",
    no_args_is_help=True,
)


def version_callback(value: bool):
    """Callback for version option."""
    if value:
        version = importlib.metadata.version("petit-cli")
        typer.echo(f"petit-cli {version}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Petit CLI - Collection of Treasure Data command-line tools."""
    pass


# Register commands
app.command("clone-db")(clone_db_command)
app.command("td2parquet")(td2parquet_command)

if __name__ == "__main__":
    app()
