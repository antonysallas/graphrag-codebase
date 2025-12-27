"""Main entry point for containerized graph building with Git cloning."""

from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from scripts._common import setup_logging
from src.config import init_config
from src.extractors import AnsibleExtractor
from src.git_utils import GitCloner
from src.graph import GraphBuilder

app = typer.Typer()
console = Console()


@app.command()
def main(
    git_url: Optional[str] = typer.Option(
        None, "--git-url", envvar="GIT_REPO_URL", help="Git repository URL to clone"
    ),
    git_branch: str = typer.Option(
        "main", "--git-branch", envvar="GIT_BRANCH", help="Git branch to checkout"
    ),
    git_token: str = typer.Option(
        "", "--git-token", envvar="GIT_TOKEN", help="Git authentication token"
    ),
    workspace: Path = typer.Option(
        Path("/workspace"), "--workspace", envvar="WORKSPACE_DIR", help="Workspace directory"
    ),
    clone_depth: int = typer.Option(1, "--clone-depth", help="Git clone depth (0 for full clone)"),
    clear: bool = typer.Option(False, "--clear", help="Clear existing graph before building"),
    workers: Optional[int] = typer.Option(
        None, "--workers", envvar="MAX_WORKERS", help="Max parallel workers"
    ),
    log_level: str = typer.Option("INFO", "--log-level", envvar="LOG_LEVEL", help="Logging level"),
) -> None:
    """Clone Git repository and build Ansible knowledge graph.

    This script is designed for containerized deployment where the Ansible
    codebase is cloned from a Git repository at runtime.

    For local development with a filesystem path, use scripts/build_graph.py instead.
    """
    setup_logging(log_level)

    console.print(
        Panel.fit(
            "[bold cyan]GraphRAG Pipeline - Clone & Build[/bold cyan]\n"
            "[dim]Ansible Codebase → Neo4j Knowledge Graph[/dim]",
            border_style="cyan",
        )
    )

    try:
        # Step 1: Load configuration
        logger.info("Loading configuration...")
        config = init_config()

        # Override workers if specified
        if workers:
            config.pipeline.max_workers = workers

        # Step 2: Clone repository
        if not git_url:
            console.print("[red]Error: GIT_REPO_URL is required[/red]")
            console.print("Set via --git-url flag or GIT_REPO_URL environment variable")
            raise typer.Exit(1)

        logger.info(f"Cloning repository: {git_url}")
        cloner = GitCloner(workspace_dir=workspace)

        try:
            codebase_path = cloner.clone_repo(
                repo_url=git_url,
                branch=git_branch,
                token=git_token if git_token else None,
                depth=clone_depth,
            )
            console.print(f"[green]✓[/green] Repository cloned to: {codebase_path}")
        except Exception as e:
            console.print(f"[red]✗ Git clone failed: {e}[/red]")
            raise typer.Exit(1)

        # Step 3: Initialize GraphBuilder
        logger.info("Connecting to Neo4j...")
        try:
            graph_builder = GraphBuilder(config=config)
            console.print(f"[green]✓[/green] Connected to Neo4j: {config.neo4j.uri}")
        except Exception as e:
            console.print(f"[red]✗ Neo4j connection failed: {e}[/red]")
            console.print("\nTroubleshooting:")
            console.print("  1. Ensure Neo4j is running")
            console.print("  2. Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
            console.print("  3. Verify network connectivity")
            raise typer.Exit(1)

        # Step 4: Initialize schema
        logger.info("Initializing Neo4j schema...")
        graph_builder.initialize_schema()

        # Clear graph if requested
        if clear:
            logger.info("Clearing existing graph data...")
            graph_builder.clear_graph()
            console.print("[yellow]⚠[/yellow] Existing graph data cleared")

        # Step 5: Extract and build graph
        logger.info(f"Starting graph extraction from: {codebase_path}")
        console.print("\n[bold]Processing Ansible codebase...[/bold]")
        console.print(f"  Workers: {config.pipeline.max_workers}")
        console.print(f"  Batch size: {config.pipeline.batch_size}\n")

        extractor = AnsibleExtractor(
            graph_builder=graph_builder,
            max_workers=config.pipeline.max_workers,
        )

        try:
            extractor.extract_codebase(codebase_path)
            console.print("\n[green]✓[/green] Extraction completed successfully")
        except Exception as e:
            console.print(f"\n[red]✗ Extraction failed: {e}[/red]")
            raise typer.Exit(1)

        # Step 6: Display summary
        logger.info("Retrieving graph statistics...")
        stats = graph_builder.get_stats()

        # Create summary table
        table = Table(title="Graph Build Summary", show_header=True, header_style="bold cyan")
        table.add_column("Node Type", style="cyan")
        table.add_column("Count", justify="right", style="green")

        for key, count in sorted(stats.items()):
            if key.startswith("nodes_"):
                node_type = key.replace("nodes_", "")
                table.add_row(node_type, str(count))

        table.add_row("", "", style="dim")
        table.add_row("[bold]TOTAL NODES", str(stats.get("total_nodes", 0)), style="bold green")

        console.print(table)

        # Relationship stats
        rel_table = Table(title="Relationships", show_header=True, header_style="bold cyan")
        rel_table.add_column("Relationship Type", style="cyan")
        rel_table.add_column("Count", justify="right", style="green")

        for key, count in sorted(stats.items()):
            if key.startswith("rels_"):
                rel_type = key.replace("rels_", "")
                rel_table.add_row(rel_type, str(count))

        rel_table.add_row("", "", style="dim")
        rel_table.add_row(
            "[bold]TOTAL RELATIONSHIPS",
            str(stats.get("total_relationships", 0)),
            style="bold green",
        )

        console.print(rel_table)

        # Final message
        console.print("\n[bold green]✓ Graph build completed successfully![/bold green]")
        console.print(f"\nNeo4j Database: [cyan]{config.neo4j.database}[/cyan]")
        console.print(f"Connection: [cyan]{config.neo4j.uri}[/cyan]")

        # Cleanup
        graph_builder.close()
        logger.info("Graph builder closed")

    except KeyboardInterrupt:
        console.print("\n[yellow]Build interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error during graph build")
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
