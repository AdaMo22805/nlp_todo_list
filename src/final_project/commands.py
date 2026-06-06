from datetime import datetime

from .models import Priority, Task
from .storage import load_tasks, save_tasks


def create_task(
    text: str,
    priority: Priority = Priority.LOW,
    due: str | None = None,
    tags: list[str] | None = None,
    raw: str | None = None,
) -> Task:
    tasks = load_tasks()
    new_id = max((t.id for t in tasks), default=0) + 1
    task = Task(
        id=new_id,
        text=text,
        due=due,
        priority=priority,
        tags=tags or [],
        created_at=_now(),
        raw=raw if raw is not None else text,
    )
    tasks.append(task)
    save_tasks(tasks)
    return task


def list_tasks(
    show_done: bool = False,
    tag: str | None = None,
) -> list[Task]:
    tasks = load_tasks()
    if not show_done:
        tasks = [t for t in tasks if not t.done]
    if tag is not None:
        tasks = [t for t in tasks if tag in t.tags]
    return tasks


def update_task(
    task_id: int,
    text: str | None = None,
    priority: Priority | None = None,
    due: str | None = None,
    tags: list[str] | None = None,
    clear_due: bool = False,
    clear_tags: bool = False,
) -> Task:
    tasks = load_tasks()
    task = _find(tasks, task_id)
    if text is not None:
        task.text = text
    if priority is not None:
        task.priority = priority
    if clear_due:
        task.due = None
    elif due is not None:
        task.due = due
    if clear_tags:
        task.tags = []
    elif tags is not None:
        task.tags = tags
    save_tasks(tasks)
    return task


def delete_task(task_id: int) -> Task:
    tasks = load_tasks()
    task = _find(tasks, task_id)
    tasks.remove(task)
    save_tasks(tasks)
    return task


def mark_done(task_id: int) -> Task:
    tasks = load_tasks()
    task = _find(tasks, task_id)
    task.done = True
    task.completed_at = _now()
    save_tasks(tasks)
    return task


def mark_undone(task_id: int) -> Task:
    tasks = load_tasks()
    task = _find(tasks, task_id)
    task.done = False
    task.completed_at = None
    save_tasks(tasks)
    return task


def clear_completed() -> list[Task]:
    tasks = load_tasks()
    removed = [t for t in tasks if t.done]
    remaining = [t for t in tasks if not t.done]
    save_tasks(remaining)
    return removed


def reset_all() -> list[Task]:
    tasks = load_tasks()
    save_tasks([])
    return tasks


def _find(tasks: list[Task], task_id: int) -> Task:
    for t in tasks:
        if t.id == task_id:
            return t
    raise ValueError(f"Task {task_id} not found")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
