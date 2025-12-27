#!/usr/bin/env python3
"""Migrate existing single-repo graph to multi-repo format."""

from pathlib import Path

import typer
from rich.console import Console

from src.config import init_config
from src.graph.builder import GraphBuilder

app = typer.Typer()
console = Console()


@app.command()
def migrate(
    default_repo: str = typer.Option(
        "default", "--default-repo", help="Repository ID to assign to existing nodes"
    ),
    config_dir: Path = typer.Option(None),
) -> None:
    """Migrate existing graph to multi-repo format."""
    config = init_config(config_dir)

    try:
        with GraphBuilder(config) as builder:
            with builder.driver.session(database=config.neo4j.database) as session:
                # Check if already migrated
                check = session.run("""
                    MATCH (n:File) WHERE n.repository IS NOT NULL
                    RETURN count(n) as count LIMIT 1
                """)
                if check.single()["count"] > 0:
                    console.print(
                        "[yellow]Graph appears to be already migrated (files have repository property)[/yellow]"
                    )
                    if not typer.confirm("Continue anyway?"):
                        raise typer.Exit(0)

                # Count nodes to migrate
                count_result = session.run("""
                    MATCH (n) WHERE n.repository IS NULL AND NOT n:Role
                    RETURN count(n) as count
                """)
                count = count_result.single()["count"]
                console.print(f"[bold]Migrating {count} nodes to repository: {default_repo}[/bold]")

                # Add repository property
                # Process in batches to avoid transaction timeouts
                batch_size = 1000
                processed = 0

                while True:
                    result = session.run(
                        """
                        MATCH (n) WHERE n.repository IS NULL AND NOT n:Role
                        WITH n LIMIT $limit
                        SET n.repository = $repo
                        RETURN count(n) as count
                    """,
                        {"repo": default_repo, "limit": batch_size},
                    )
                    batch_count = result.single()["count"]
                    processed += batch_count

                    if batch_count == 0:
                        break

                    console.print(f"Processed {processed} nodes...")

                console.print(f"[green]Added repository property to {processed} nodes[/green]")

                # Drop old constraint (if exists)
                try:
                    session.run("DROP CONSTRAINT unique_file_path IF EXISTS")
                    console.print("[dim]Dropped old unique_file_path constraint[/dim]")
                except Exception as e:
                    console.print(f"[dim]Note: Could not drop old constraint: {e}[/dim]")

                # Note: New constraints are created by GraphBuilder.initialize_schema()
                # or explicitly here. The builder creates constraints based on schema config.
                # Since we updated the schema, let's trigger initialization.
                builder.initialize_schema()

                console.print("[bold green]Migration complete![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
