import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

load_dotenv()

console = Console()


@click.command()
@click.option(
    "--source",
    required=True,
    help="Current Kubernetes version, e.g. 1.27",
)
@click.option(
    "--target",
    required=True,
    help="Target Kubernetes version, e.g. 1.30",
)
@click.option(
    "--kubeconfig",
    default=None,
    envvar="KUBECONFIG",
    help="Path to kubeconfig (defaults to KUBECONFIG env var or ~/.kube/config)",
)
@click.option(
    "--api-key",
    default=None,
    envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var)",
)
@click.option(
    "--model",
    default=None,
    envvar="CLAUDE_MODEL",
    help="Claude model ID (default: claude-sonnet-4-6)",
)
@click.option(
    "--output-dir",
    default="reports",
    show_default=True,
    help="Directory to save the assessment report",
)
@click.option(
    "--no-stream",
    is_flag=True,
    default=False,
    help="Disable streaming output (wait for full response)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Collect cluster data only — do not call Claude",
)
def main(
    source: str,
    target: str,
    kubeconfig: str | None,
    api_key: str | None,
    model: str | None,
    output_dir: str,
    no_stream: bool,
    dry_run: bool,
) -> None:
    """Kubernetes upgrade feasibility and risk assessment powered by Claude."""
    from k8s_upgrade_analyzer import collector, claude, reporter

    console.print(
        Panel.fit(
            f"[bold]K8s Upgrade Analyzer[/bold]\n"
            f"[dim]{source}[/dim] → [green]{target}[/green]",
            border_style="blue",
        )
    )

    # --- Step 1: collect cluster data ---
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Collecting cluster data...", total=None)
        snapshot = collector.collect(kubeconfig=kubeconfig)
        progress.update(task, description="Collection complete")

    if snapshot.errors:
        console.print(
            f"[yellow]Collection warnings ({len(snapshot.errors)}):[/yellow]"
        )
        for err in snapshot.errors:
            console.print(f"  [dim]{err}[/dim]")

    if dry_run:
        console.print("[green]Dry-run complete.[/green] Cluster snapshot collected; skipping Claude analysis.")
        return

    if not api_key:
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            console.print(
                "[red]Error:[/red] ANTHROPIC_API_KEY is not set.\n"
                "Set it in .env or pass --api-key."
            )
            sys.exit(1)

    # --- Step 2: analyze with Claude ---
    console.print("\n[bold]Running assessment with Claude…[/bold]\n")
    try:
        raw = claude.analyze(
            source_version=source,
            target_version=target,
            snapshot=snapshot,
            api_key=api_key,
            model=model,
            stream=not no_stream,
        )
    except Exception as exc:
        console.print(f"[red]Claude API error:[/red] {exc}")
        sys.exit(1)

    # --- Step 3: save report ---
    report_path = reporter.save(
        raw_analysis=raw,
        source_version=source,
        target_version=target,
        output_dir=output_dir,
    )
    console.print(f"\n[green]Report saved:[/green] {report_path}")


if __name__ == "__main__":
    main()
