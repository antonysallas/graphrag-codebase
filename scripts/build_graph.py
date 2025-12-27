#!/usr/bin/env python3
"""Build graph from Ansible codebase."""

import re
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Import extractors to register them
import src.extractors.ansible  # noqa
import src.extractors.generic  # noqa
import src.extractors.python  # noqa
from scripts._common import setup_logging
from src.config import init_config
from src.extractors.registry import ExtractorRegistry, detect_repo_type
from src.graph import GraphBuilder, Node, NodeType, Relationship, RelationshipType

app = typer.Typer()
console = Console()


@app.command()
def build(
    codebase_path: Path = typer.Argument(..., help="Path to Ansible codebase"),
    config_dir: Path = typer.Option(None, help="Path to config directory"),
    clear: bool = typer.Option(False, "--clear", help="Clear existing graph before building"),
    max_workers: int = typer.Option(
        None, "--workers", help="Maximum parallel workers (default: from config)"
    ),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
    repo_type: str = typer.Option(
        "auto", "--repo-type", help="Repository type (ansible, python, generic, auto)"
    ),
    repo_id: str = typer.Option(
        None,
        "--repo-id",
        help="Repository identifier (auto-detected from directory name if not provided)",
    ),
) -> None:
    """Build Neo4j graph from Ansible codebase.

    This command parses all files in the Ansible codebase and builds
    a comprehensive graph database representing the codebase structure.
    """
    setup_logging(log_level)

    console.print("\n[bold blue]GraphRAG Pipeline - Build Graph[/bold blue]\n")

    # Validate codebase path
    if not codebase_path.exists():
        console.print(f"[red]Error: Codebase path does not exist: {codebase_path}[/red]")
        raise typer.Exit(1)

    # Auto-detect repo_id from directory name if not provided
    if repo_id is None:
        repo_id = codebase_path.name
        console.print(f"[bold]Auto-detected repository ID: {repo_id}[/bold]")

    # Validate format
    if not re.match(r"^[a-zA-Z0-9_-]+$", repo_id):
        console.print(
            f"[red]Invalid repo ID: {repo_id}. Use alphanumeric, hyphens, underscores.[/red]"
        )
        raise typer.Exit(1)

    # Initialize configuration
    config = init_config(config_dir)
    console.print("[green]✓[/green] Configuration loaded")

    # Use config value if max_workers not specified
    if max_workers is None:
        max_workers = config.pipeline.max_workers

    # Determine repo type and extractor
    final_repo_type = repo_type
    try:
        if repo_type == "auto":
            detection_result = detect_repo_type(codebase_path)
            detected_type = detection_result.repo_type
            confidence = detection_result.confidence
            console.print(
                f"[bold]Auto-detected repo type: {detected_type} (confidence: {confidence:.2f})[/bold]"
            )
            final_repo_type = detected_type

            # Check if we have an extractor (Registry.get_extractor raises ValueError if not found)
            ExtractorRegistry.get_extractor(detected_type)
        else:
            console.print(f"[bold]Using specified repo type: {repo_type}[/bold]")
            ExtractorRegistry.get_extractor(repo_type)  # Verify it exists

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Failed to determine extractor: {e}")
        raise typer.Exit(1)

    # Display configuration
    config_table = Table(title="Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="yellow")

    config_table.add_row("Neo4j URI", config.neo4j.uri)
    config_table.add_row("Neo4j Database", config.neo4j.database)
    config_table.add_row("Codebase Path", str(codebase_path.absolute()))
    config_table.add_row("Repository ID", repo_id)
    config_table.add_row("Max Workers", str(max_workers))
    config_table.add_row("Batch Size", str(config.pipeline.batch_size))
    config_table.add_row(
        "Repo Type", repo_type if repo_type != "auto" else f"auto ({final_repo_type})"
    )

    console.print(config_table)
    console.print()

    try:
        # Initialize graph builder
        with GraphBuilder(config, schema_profile=final_repo_type) as graph_builder:
            console.print("[bold]Initializing database schema...[/bold]")
            graph_builder.initialize_schema()
            console.print("[green]✓[/green] Schema initialized\n")

            # Clear graph if requested
            if clear:
                console.print(
                    f"[bold yellow]Clearing existing nodes for repository: {repo_id}...[/bold yellow]"
                )
                if typer.confirm(f"Are you sure you want to clear all nodes for repo '{repo_id}'?"):
                    # Custom clear for repo
                    with graph_builder.driver.session(database=config.neo4j.database) as session:
                        count_result = session.run(
                            """
                            MATCH (n) WHERE n.repository = $repo AND NOT n:Role
                            RETURN count(n) as count
                        """,
                            {"repo": repo_id},
                        )
                        count = count_result.single()["count"]

                        session.run(
                            """
                            MATCH (n) WHERE n.repository = $repo AND NOT n:Role
                            DETACH DELETE n
                        """,
                            {"repo": repo_id},
                        )
                        console.print(
                            f"[green]✓[/green] Cleared {count} nodes for repository: {repo_id}\n"
                        )
                else:
                    console.print("[yellow]Skipping clear[/yellow]\n")

            # Extract codebase
            console.print("[bold]Extracting codebase...[/bold]")

            extractor_cls = ExtractorRegistry.get_extractor(final_repo_type)
            # Initialize extractor. Pass max_workers only if accepted (AnsibleExtractor)
            # Or assume standard init. BaseExtractor doesn't take args.
            # AnsibleExtractor takes max_workers.
            # We can check signature or just try?
            # Or rely on kwargs.
            try:
                extractor = extractor_cls(max_workers=max_workers)
            except TypeError:
                extractor = extractor_cls()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Processing nodes...", total=None)

                # Extract nodes
                for entity in extractor.extract(codebase_path, repository_id=repo_id):
                    try:
                        node_type = NodeType(entity["type"])
                        node = Node(node_type=node_type, properties=entity["properties"])
                        graph_builder.add_node(node)
                    except ValueError:
                        logger.warning(f"Unknown node type: {entity['type']}")

                progress.update(task, description="Processing relationships...")

                # Extract relationships
                for rel_data in extractor.extract_relationships(
                    codebase_path, repository_id=repo_id
                ):
                    try:
                        rel_type = RelationshipType(rel_data["type"])

                        src_type = NodeType(rel_data["source"]["type"])
                        src_node = Node(
                            node_type=src_type, properties=rel_data["source"]["properties"]
                        )

                        tgt_type = NodeType(rel_data["target"]["type"])
                        tgt_node = Node(
                            node_type=tgt_type, properties=rel_data["target"]["properties"]
                        )

                        rel = Relationship(
                            rel_type=rel_type,
                            from_node=src_node,
                            to_node=tgt_node,
                            properties=rel_data.get("properties", {}),
                        )
                        graph_builder.add_relationship(rel)
                    except ValueError as e:
                        logger.warning(f"Error creating relationship: {e}")

                progress.update(task, completed=True)

            console.print("[green]✓[/green] Extraction complete\n")

            # Get and display statistics
            console.print("[bold]Collecting graph statistics...[/bold]")
            stats = graph_builder.get_stats()

            stats_table = Table(title="Graph Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Count", style="green", justify="right")

            # Total counts
            stats_table.add_row("Total Nodes", str(stats.get("total_nodes", 0)))
            stats_table.add_row("Total Relationships", str(stats.get("total_relationships", 0)))
            stats_table.add_section()

            # Dynamic stats display
            for key, value in sorted(stats.items()):
                if key.startswith("nodes_"):
                    display_key = key.replace("nodes_", "")
                    stats_table.add_row(display_key, str(value))

            console.print(stats_table)

        console.print("\n[bold green]✓ Graph build complete![/bold green]\n")

    except Exception as e:
        logger.exception("Build failed")
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise typer.Exit(1)


@app.command(name="list-repos")
def list_repos(config_dir: Path = typer.Option(None, help="Path to config directory")) -> None:
    """List all indexed repositories with node counts."""
    config = init_config(config_dir)

    try:
        with GraphBuilder(config) as builder:
            with builder.driver.session(database=config.neo4j.database) as session:
                result = session.run(
                    """
                    MATCH (n)
                    WHERE n.repository IS NOT NULL
                    RETURN n.repository as repository,
                           labels(n)[0] as type,
                           count(n) as count
                    ORDER BY repository, type
                """,
                )

                # Group and display as table
                from rich.table import Table

                table = Table(title="Indexed Repositories")
                table.add_column("Repository", style="green")
                table.add_column("Node Type", style="cyan")
                table.add_column("Count", justify="right")

                for record in result:
                    table.add_row(record["repository"], record["type"], str(record["count"]))

                console.print(table)
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise typer.Exit(1)


@app.command(name="clear-repo")
def clear_repo(
    repo_id: str = typer.Argument(..., help="Repository ID to clear"),
    config_dir: Path = typer.Option(None, help="Path to config directory"),
) -> None:
    """Clear all nodes for a specific repository (keeps shared Roles)."""
    config = init_config(config_dir)

    try:
        with GraphBuilder(config) as builder:
            with builder.driver.session(database=config.neo4j.database) as session:
                # Count before
                count_result = session.run(
                    """
                    MATCH (n) WHERE n.repository = $repo AND NOT n:Role
                    RETURN count(n) as count
                """,
                    {"repo": repo_id},
                )
                count = count_result.single()["count"]

                if count == 0:
                    console.print(f"[yellow]No nodes found for repository: {repo_id}[/yellow]")
                    return

                if typer.confirm(
                    f"Are you sure you want to delete {count} nodes from repository '{repo_id}'?"
                ):
                    # Delete
                    session.run(
                        """
                        MATCH (n) WHERE n.repository = $repo AND NOT n:Role
                        DETACH DELETE n
                    """,
                        {"repo": repo_id},
                    )

                    console.print(
                        f"[green]Cleared {count} nodes from repository: {repo_id}[/green]"
                    )
                else:
                    console.print("[yellow]Operation cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise typer.Exit(1)


@app.command()
def stats(
    config_dir: Path = typer.Option(None, help="Path to config directory"),
) -> None:
    """Display graph statistics."""
    setup_logging("WARNING")

    console.print("\n[bold blue]GraphRAG Pipeline - Statistics[/bold blue]\n")

    # Initialize configuration
    config = init_config(config_dir)

    try:
        with GraphBuilder(config) as graph_builder:
            stats = graph_builder.get_stats()

            stats_table = Table(title="Graph Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Count", style="green", justify="right")

            for key, value in sorted(stats.items()):
                # Format key for display
                display_key = key.replace("_", " ").title()
                stats_table.add_row(display_key, str(value))

            console.print(stats_table)
            console.print()

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise typer.Exit(1)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
