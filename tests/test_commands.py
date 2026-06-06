import pytest

from final_project.commands import (
    clear_completed,
    create_task,
    delete_task,
    list_tasks,
    mark_done,
    mark_undone,
    reset_all,
    update_task,
)
from final_project.models import Priority


def test_create_task_defaults(todo_file):
    task = create_task("buy milk")
    assert task.id == 1
    assert task.text == "buy milk"
    assert task.priority is Priority.LOW
    assert task.due is None
    assert task.tags == []
    assert task.done is False
    assert task.completed_at is None
    assert task.created_at


def test_create_task_with_options(todo_file):
    task = create_task(
        "study",
        priority=Priority.HIGH,
        due="2026-06-10",
        tags=["school"],
    )
    assert task.priority is Priority.HIGH
    assert task.due == "2026-06-10"
    assert task.tags == ["school"]


def test_create_task_raw_defaults_to_text(todo_file):
    task = create_task("buy milk")
    assert task.raw == "buy milk"


def test_create_task_raw_can_differ_from_text(todo_file):
    task = create_task("buy milk", raw="buy milk tomorrow")
    assert task.text == "buy milk"
    assert task.raw == "buy milk tomorrow"


def test_create_task_assigns_sequential_ids(todo_file):
    a = create_task("a")
    b = create_task("b")
    c = create_task("c")
    assert [a.id, b.id, c.id] == [1, 2, 3]


def test_create_task_persists_across_calls(todo_file):
    create_task("a")
    create_task("b")
    assert [t.text for t in list_tasks()] == ["a", "b"]


def test_list_tasks_default_hides_done(todo_file):
    create_task("a")
    create_task("b")
    mark_done(1)
    assert [t.id for t in list_tasks()] == [2]


def test_list_tasks_show_done_includes_all(todo_file):
    create_task("a")
    create_task("b")
    mark_done(1)
    assert [t.id for t in list_tasks(show_done=True)] == [1, 2]


def test_list_tasks_filter_by_tag(todo_file):
    create_task("a", tags=["school"])
    create_task("b", tags=["work"])
    create_task("c", tags=["school", "personal"])
    assert [t.id for t in list_tasks(tag="school")] == [1, 3]


def test_list_tasks_empty(todo_file):
    assert list_tasks() == []


def test_update_task_changes_only_supplied_fields(todo_file):
    create_task("a", priority=Priority.LOW, tags=["x"])
    updated = update_task(1, text="A!")
    assert updated.text == "A!"
    assert updated.priority is Priority.LOW
    assert updated.tags == ["x"]


def test_update_task_all_fields(todo_file):
    create_task("a")
    updated = update_task(
        1,
        text="A",
        priority=Priority.HIGH,
        due="2026-06-10",
        tags=["school"],
    )
    assert updated.text == "A"
    assert updated.priority is Priority.HIGH
    assert updated.due == "2026-06-10"
    assert updated.tags == ["school"]


def test_update_task_persists(todo_file):
    create_task("a")
    update_task(1, text="A")
    [loaded] = list_tasks()
    assert loaded.text == "A"


def test_update_task_not_found_raises(todo_file):
    with pytest.raises(ValueError, match="999"):
        update_task(999, text="x")


def test_update_task_clear_due(todo_file):
    create_task("a", due="2026-06-10")
    updated = update_task(1, clear_due=True)
    assert updated.due is None


def test_update_task_clear_tags(todo_file):
    create_task("a", tags=["school", "work"])
    updated = update_task(1, clear_tags=True)
    assert updated.tags == []


def test_update_task_clear_due_overrides_due_arg(todo_file):
    create_task("a", due="2026-06-10")
    updated = update_task(1, due="2026-07-01", clear_due=True)
    assert updated.due is None


def test_delete_task_removes_from_list(todo_file):
    create_task("a")
    create_task("b")
    delete_task(1)
    assert [t.id for t in list_tasks()] == [2]


def test_delete_task_returns_removed_task(todo_file):
    create_task("a")
    removed = delete_task(1)
    assert removed.text == "a"


def test_delete_task_not_found_raises(todo_file):
    with pytest.raises(ValueError, match="999"):
        delete_task(999)


def test_mark_done_sets_flag_and_timestamp(todo_file):
    create_task("a")
    done = mark_done(1)
    assert done.done is True
    assert done.completed_at


def test_mark_done_persists(todo_file):
    create_task("a")
    mark_done(1)
    [loaded] = list_tasks(show_done=True)
    assert loaded.done is True


def test_mark_done_not_found_raises(todo_file):
    with pytest.raises(ValueError, match="999"):
        mark_done(999)


def test_mark_undone_clears_state(todo_file):
    create_task("a")
    mark_done(1)
    undone = mark_undone(1)
    assert undone.done is False
    assert undone.completed_at is None


def test_mark_undone_persists(todo_file):
    create_task("a")
    mark_done(1)
    mark_undone(1)
    [loaded] = list_tasks()
    assert loaded.done is False


def test_mark_undone_not_found_raises(todo_file):
    with pytest.raises(ValueError, match="999"):
        mark_undone(999)


def test_clear_completed_removes_only_done(todo_file):
    create_task("a")
    create_task("b")
    create_task("c")
    mark_done(1)
    mark_done(3)
    removed = clear_completed()
    assert [t.id for t in removed] == [1, 3]
    assert [t.id for t in list_tasks(show_done=True)] == [2]


def test_clear_completed_returns_empty_when_nothing_done(todo_file):
    create_task("a")
    assert clear_completed() == []
    assert [t.id for t in list_tasks()] == [1]


def test_reset_all_removes_done_and_pending(todo_file):
    create_task("a")
    create_task("b")
    create_task("c")
    mark_done(1)
    removed = reset_all()
    assert {t.id for t in removed} == {1, 2, 3}
    assert list_tasks(show_done=True) == []


def test_reset_all_empty(todo_file):
    assert reset_all() == []


def test_reset_all_then_create_starts_id_at_1(todo_file):
    create_task("a")
    create_task("b")
    reset_all()
    new = create_task("c")
    assert new.id == 1
