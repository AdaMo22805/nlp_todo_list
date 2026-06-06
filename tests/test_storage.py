import json

from final_project.models import Priority, Task
from final_project.storage import load_tasks, save_tasks


def test_load_returns_empty_when_file_missing(todo_file):
    assert load_tasks() == []


def test_save_creates_file(todo_file):
    save_tasks([Task(id=1, text="a")])
    assert todo_file.exists()


def test_roundtrip_preserves_all_fields(todo_file):
    original = Task(
        id=1,
        text="finish project",
        due="2026-06-10",
        priority=Priority.HIGH,
        tags=["school", "personal"],
        done=True,
        created_at="2026-06-05T10:00:00",
        completed_at="2026-06-05T11:00:00",
        raw="finish project by tomorrow",
    )
    save_tasks([original])
    assert load_tasks() == [original]


def test_priority_deserializes_to_enum(todo_file):
    save_tasks([Task(id=1, text="a", priority=Priority.HIGH)])
    [loaded] = load_tasks()
    assert loaded.priority is Priority.HIGH


def test_save_writes_valid_json(todo_file):
    save_tasks([Task(id=1, text="a")])
    parsed = json.loads(todo_file.read_text())
    assert isinstance(parsed, list)
    assert parsed[0]["id"] == 1
    assert parsed[0]["priority"] == "low"
