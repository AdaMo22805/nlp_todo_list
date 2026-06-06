from datetime import date
from typing import Annotated

import typer
from dateutil import parser as dateutil_parser
from rich.console import Console
from rich.table import Table

from . import commands as core
from .models import Priority, Task

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    context_settings={"help_option_names": ["--help"]},
    help="Smart todo list with NLP-friendly input.",
)
console = Console()


_PRIORITY_RANK = {
    Priority.HIGH: 0,
    Priority.MED: 1,
    Priority.LOW: 2,
    Priority.NEVER: 3,
}
_PRIORITY_STYLE = {
    Priority.HIGH: "bold red",
    Priority.MED: "yellow",
    Priority.LOW: "white",
    Priority.NEVER: "grey50",
}


def _resolve_priority_flags(
    never: bool, low: bool, med: bool, high: bool
) -> Priority | None:
    selected = [
        p
        for p, on in [
            (Priority.NEVER, never),
            (Priority.LOW, low),
            (Priority.MED, med),
            (Priority.HIGH, high),
        ]
        if on
    ]
    if len(selected) > 1:
        raise typer.BadParameter(
            "Only one priority flag (-n / -l / -m / -h) may be used."
        )
    return selected[0] if selected else None


def _parse_due(s: str) -> str:
    try:
        return dateutil_parser.parse(s).date().isoformat()
    except (ValueError, OverflowError) as e:
        raise typer.BadParameter(f"Could not parse due date {s!r}: {e}") from e


def _abort_on_value_error(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def add(
    text: Annotated[str, typer.Argument(help="Task description")],
    never: Annotated[
        bool, typer.Option("-n", help="Never priority (also clears due date)")
    ] = False,
    low: Annotated[bool, typer.Option("-l", help="Low priority (default)")] = False,
    med: Annotated[bool, typer.Option("-m", help="Medium priority")] = False,
    high: Annotated[bool, typer.Option("-h", help="High priority")] = False,
    due: Annotated[
        str | None,
        typer.Option("--due", help="Due date (e.g. 2026-06-10)"),
    ] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option("--tag", help="Tag (repeatable)"),
    ] = None,
) -> None:
    """Add a new task."""
    priority = _resolve_priority_flags(never, low, med, high) or Priority.LOW
    due_iso = None if priority is Priority.NEVER else (_parse_due(due) if due else None)
    task = core.create_task(
        text=text,
        priority=priority,
        due=due_iso,
        tags=list(tag) if tag else [],
    )
    console.print(f"[green]+[/green] Added [cyan]#{task.id}[/cyan] {task.text}")


@app.command(name="ls")
def ls(
    all_: Annotated[
        bool, typer.Option("--all", "-a", help="Include completed tasks")
    ] = False,
    done_only: Annotated[
        bool, typer.Option("--done", help="Show only completed tasks")
    ] = False,
    tag: Annotated[
        str | None, typer.Option("--tag", help="Filter by tag")
    ] = None,
    priority: Annotated[
        Priority | None, typer.Option("--priority", help="Filter by priority")
    ] = None,
    group_by_tag: Annotated[
        bool,
        typer.Option(
            "--group-by-tag",
            "-g",
            help="Group output by tag, sorted by priority within each",
        ),
    ] = False,
) -> None:
    """List tasks."""
    show_done = all_ or done_only
    tasks = core.list_tasks(show_done=show_done)
    if done_only:
        tasks = [t for t in tasks if t.done]
    if tag:
        tasks = [t for t in tasks if tag in t.tags]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]

    if not tasks:
        console.print("[dim]No tasks.[/dim]")
        return

    if group_by_tag:
        _render_grouped(tasks)
    else:
        _render_table(tasks)


def _sort_key(t: Task) -> tuple:
    has_due = 0 if t.due is not None else 1
    return (has_due, t.due or "", _PRIORITY_RANK[t.priority], t.id)


def _render_table(tasks: list[Task], title: str | None = None) -> None:
    today_iso = date.today().isoformat()
    table = Table(title=title, title_justify="left", show_lines=False)
    table.add_column("✓", justify="center", width=1)
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Priority", no_wrap=True)
    table.add_column("Due", no_wrap=True)
    table.add_column("Task")
    table.add_column("Tags", style="magenta")

    for t in sorted(tasks, key=_sort_key):
        check = "[green]✓[/green]" if t.done else " "
        prio_style = _PRIORITY_STYLE[t.priority]
        prio = f"[{prio_style}]{t.priority.value}[/{prio_style}]"
        if t.due is None:
            due_disp = "[dim]—[/dim]"
        elif not t.done and t.due < today_iso:
            due_disp = f"[red]{t.due}[/red]"
        else:
            due_disp = t.due
        text_disp = f"[dim strike]{t.text}[/dim strike]" if t.done else t.text
        tags_disp = " ".join(f"#{tg}" for tg in t.tags)
        table.add_row(check, str(t.id), prio, due_disp, text_disp, tags_disp)
    console.print(table)


def _render_grouped(tasks: list[Task]) -> None:
    groups: dict[str, list[Task]] = {}
    for t in tasks:
        if not t.tags:
            groups.setdefault("(untagged)", []).append(t)
        else:
            for tg in t.tags:
                groups.setdefault(tg, []).append(t)
    for name in sorted(groups.keys()):
        _render_table(groups[name], title=f"[bold magenta]#{name}[/bold magenta]")


@app.command()
def done(
    task_id: Annotated[int, typer.Argument(help="Task ID")],
) -> None:
    """Mark a task done."""
    task = _abort_on_value_error(core.mark_done, task_id)
    console.print(f"[green]✓[/green] Done [cyan]#{task.id}[/cyan] {task.text}")


@app.command()
def undone(
    task_id: Annotated[int, typer.Argument(help="Task ID")],
) -> None:
    """Mark a task not done."""
    task = _abort_on_value_error(core.mark_undone, task_id)
    console.print(f"↻ Reopened [cyan]#{task.id}[/cyan] {task.text}")


@app.command()
def edit(
    task_id: Annotated[int, typer.Argument(help="Task ID")],
    text: Annotated[
        str | None, typer.Option("--text", help="New task description")
    ] = None,
    never: Annotated[bool, typer.Option("-n", help="Set never priority")] = False,
    low: Annotated[bool, typer.Option("-l", help="Set low priority")] = False,
    med: Annotated[bool, typer.Option("-m", help="Set medium priority")] = False,
    high: Annotated[bool, typer.Option("-h", help="Set high priority")] = False,
    due: Annotated[
        str | None, typer.Option("--due", help="New due date")
    ] = None,
    no_date: Annotated[
        bool, typer.Option("--no-date", help="Clear due date")
    ] = False,
    tag: Annotated[
        list[str] | None,
        typer.Option("--tag", help="Replace tags (repeatable)"),
    ] = None,
    no_tags: Annotated[
        bool, typer.Option("--no-tags", help="Clear all tags")
    ] = False,
) -> None:
    """Edit a task."""
    if due and no_date:
        raise typer.BadParameter("--due and --no-date are mutually exclusive.")
    if tag and no_tags:
        raise typer.BadParameter("--tag and --no-tags are mutually exclusive.")

    priority = _resolve_priority_flags(never, low, med, high)
    clear_due = no_date or priority is Priority.NEVER
    due_iso = None if clear_due else (_parse_due(due) if due else None)

    task = _abort_on_value_error(
        core.update_task,
        task_id,
        text=text,
        priority=priority,
        due=due_iso,
        tags=list(tag) if tag else None,
        clear_due=clear_due,
        clear_tags=no_tags,
    )
    console.print(f"[green]~[/green] Updated [cyan]#{task.id}[/cyan] {task.text}")


@app.command()
def rm(
    task_id: Annotated[int, typer.Argument(help="Task ID")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """Delete a task."""
    preview = _abort_on_value_error(_peek, task_id)
    if not yes and not typer.confirm(
        f"Delete task #{preview.id} '{preview.text}'?", default=False
    ):
        console.print("[dim]Aborted.[/dim]")
        raise typer.Exit(0)
    task = _abort_on_value_error(core.delete_task, task_id)
    console.print(f"[red]-[/red] Deleted [cyan]#{task.id}[/cyan] {task.text}")


@app.command()
def clear(
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """Delete all completed tasks."""
    done_tasks = [t for t in core.list_tasks(show_done=True) if t.done]
    if not done_tasks:
        console.print("[dim]No completed tasks to clear.[/dim]")
        return
    if not yes and not typer.confirm(
        f"Delete {len(done_tasks)} completed task(s)?", default=False
    ):
        console.print("[dim]Aborted.[/dim]")
        raise typer.Exit(0)
    removed = core.clear_completed()
    console.print(f"[red]-[/red] Cleared {len(removed)} completed task(s).")


def _peek(task_id: int) -> Task:
    for t in core.list_tasks(show_done=True):
        if t.id == task_id:
            return t
    raise ValueError(f"Task {task_id} not found")
