"""
OmniWrite — Command Line Interface
"""

from __future__ import annotations

import asyncio
import time
from uuid import uuid4

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from backend.agents.graph import create_graph
from backend.core.config import get_settings
from backend.models.request import GenerateRequest, ModelMode, Platform
from backend.models.state import AgentState

app = typer.Typer(help="OmniWrite: Agentic multi-platform content generation tool")
console = Console()


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


@app.command()
def generate(
    topic: str = typer.Argument(..., help="The main topic or brief for content generation"),
    platforms: str = typer.Option(
        "blog,linkedin,reddit",
        help="Comma-separated list of target platforms (blog, linkedin, reddit, linkedin_comment)",
    ),
    model: str = typer.Option(
        "test",
        help="LLM model mode to use (test, production, local, groq)",
    ),
    skip_research: bool = typer.Option(
        False,
        "--skip-research",
        help="Skip web research, generate based on brief/topic only",
    ),
    skip_outline_approval: bool = typer.Option(
        True,
        "--skip-outline",
        help="Skip outline approval (runs the pipeline fully to completion)",
    ),
    additional_context: str = typer.Option(
        "",
        "--context",
        help="Additional context or background information for generation",
    ),
):
    """
    Generate content for multiple platforms from a single topic/brief.
    """
    settings = get_settings()

    # Parse platforms
    parsed_platforms = []
    for p in platforms.split(","):
        p_clean = p.strip().lower()
        try:
            parsed_platforms.append(Platform(p_clean))
        except ValueError:
            console.print(f"[red]Error: Invalid platform '{p_clean}'[/red]")
            raise typer.Exit(code=1)

    # Parse model mode
    try:
        model_mode = ModelMode(model.strip().lower())
    except ValueError:
        console.print(f"[red]Error: Invalid model mode '{model}'[/red]")
        raise typer.Exit(code=1)

    # Override settings default_mode
    settings.default_mode = model_mode.value

    # Build GenerateRequest
    request = GenerateRequest(
        topic=topic,
        additional_context=additional_context,
        platforms=parsed_platforms,
        model_mode=model_mode,
        skip_research=skip_research,
        skip_outline_approval=skip_outline_approval,
    )

    # If skip_outline_approval is False, note that CLI currently runs in batch mode
    if not skip_outline_approval:
        console.print(
            "[yellow]Warning: Running in interactive outline approval mode via CLI. "
            "You will be prompted to approve the outline before proceeding.[/yellow]"
        )

    # Create job ID
    job_id = uuid4()

    # Set up initial agent state
    initial_state = AgentState(
        job_id=job_id,
        request=request,
        brand=None,
        start_time=time.time(),
    )
    if skip_outline_approval:
        initial_state.outline_approved = True

    console.print(
        Panel(
            f"[bold green]Starting generation pipeline[/bold green]\n"
            f"[bold]Topic:[/bold] {topic}\n"
            f"[bold]Platforms:[/bold] {', '.join(p.value for p in parsed_platforms)}\n"
            f"[bold]Model Mode:[/bold] {model_mode.value}\n"
            f"[bold]Research Enabled:[/bold] {not skip_research}",
            title="OmniWrite CLI",
            border_style="indigo",
        )
    )

    async def _execute():
        graph = create_graph(settings)
        state_dict = initial_state.model_dump(mode="json")

        current_state_dict = state_dict

        # Stream step events
        async for event in graph.astream(state_dict):
            for node_name, node_state in event.items():
                if not isinstance(node_state, dict):
                    continue
                current_state_dict = node_state

                steps = node_state.get("steps", [])
                if steps:
                    last_step = steps[-1]
                    status_emoji = "✅" if last_step.get("status") == "complete" else "⏳"
                    console.print(
                        f"{status_emoji} [cyan]{last_step.get('agent', node_name)}[/cyan]: "
                        f"{last_step.get('message', '')}"
                    )

                # Check for interactive outline approval
                if (
                    not skip_outline_approval
                    and not node_state.get("outline_approved", True)
                    and node_state.get("outline")
                ):
                    console.print("\n[bold yellow]--- Proposed Outline ---[/bold yellow]")
                    console.print(node_state["outline"])
                    console.print("[bold yellow]------------------------[/bold yellow]\n")

                    approve = typer.confirm("Do you approve this outline?")
                    if not approve:
                        console.print("[red]Outline rejected. Aborting generation.[/red]")
                        raise typer.Exit(code=0)

                    # Set approved to True and re-run
                    node_state["outline_approved"] = True
                    # Continue execution with updated state
                    # We resume the remainder of the pipeline (writers -> editor) manually
                    from backend.agents.blog_writer import write_blog
                    from backend.agents.editor_agent import run_editor
                    from backend.agents.linkedin_commenter import write_linkedin_comment
                    from backend.agents.linkedin_writer import write_linkedin
                    from backend.agents.reddit_writer import write_reddit

                    state = AgentState(**node_state)

                    platforms_to_write = {p.value for p in request.platforms}
                    if "blog" in platforms_to_write:
                        console.print("⏳ [cyan]blog_writer[/cyan]: Writing blog post...")
                        state = await write_blog(state, settings)
                    if "reddit" in platforms_to_write:
                        console.print("⏳ [cyan]reddit_writer[/cyan]: Writing Reddit post...")
                        state = await write_reddit(state, settings)
                    if "linkedin" in platforms_to_write:
                        console.print("⏳ [cyan]linkedin_writer[/cyan]: Writing LinkedIn post...")
                        state = await write_linkedin(state, settings)
                    if "linkedin_comment" in platforms_to_write:
                        console.print(
                            "⏳ [cyan]linkedin_commenter[/cyan]: Writing LinkedIn comment..."
                        )
                        state = await write_linkedin_comment(state, settings)

                    console.print("⏳ [cyan]editor_agent[/cyan]: Editing and polishing content...")
                    state = await run_editor(state, settings)
                    current_state_dict = state.model_dump(mode="json")
                    break

        # Final presentation
        console.print("\n[bold green]🎉 Generation completed successfully![/bold green]\n")

        outputs = current_state_dict.get("outputs", {})
        for platform_name, output_data in outputs.items():
            content = output_data.get("content", "")
            word_count = output_data.get("word_count", 0)

            console.print(
                Panel(
                    content,
                    title=f"[bold uppercase]{platform_name}[/bold uppercase] ({word_count} words)",
                    border_style="green",
                    expand=False,
                )
            )

        # Cost tracking table
        cost_table = Table(title="Cost and Token Summary")
        cost_table.add_column("Metric", style="cyan")
        cost_table.add_column("Value", style="magenta")

        cost_table.add_row(
            "Total Input Tokens", str(current_state_dict.get("total_input_tokens", 0))
        )
        cost_table.add_row(
            "Total Output Tokens", str(current_state_dict.get("total_output_tokens", 0))
        )
        cost_table.add_row("Total Cost", f"${current_state_dict.get('total_cost_usd', 0.0):.5f}")

        console.print(cost_table)

    run_async(_execute())


if __name__ == "__main__":
    app()
