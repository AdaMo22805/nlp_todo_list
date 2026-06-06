import json
import os
from dataclasses import asdict
from pathlib import Path

from .models import Priority, Task

STORAGE_PATH = Path(os.environ.get("TODO_FILE", Path.home() / ".todo.json"))


def load_tasks() -> list[Task]:
    if not STORAGE_PATH.exists():
        return []
    with STORAGE_PATH.open() as f:
        data = json.load(f)
    return [_task_from_dict(d) for d in data]


def save_tasks(tasks: list[Task]) -> None:
    STORAGE_PATH.write_text(
        json.dumps([asdict(t) for t in tasks], indent=2)
    )


def _task_from_dict(d: dict) -> Task:
    return Task(
        id=d["id"],
        text=d["text"],
        due=d.get("due"),
        priority=Priority(d.get("priority", Priority.LOW)),
        tags=d.get("tags", []),
        done=d.get("done", False),
        created_at=d.get("created_at", ""),
        completed_at=d.get("completed_at"),
        raw=d.get("raw", ""),
    )
