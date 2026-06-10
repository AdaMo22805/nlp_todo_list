import json
import re

from typer.testing import CliRunner

from final_project.cli import app

runner = CliRunner()


def _clean(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def _ls(args: list[str] | None = None) -> str:
    result = runner.invoke(app, ["ls", *(args or [])])
    assert result.exit_code == 0
    return _clean(result.output)


# ---------- add ----------

def test_add_basic(todo_file):
    result = runner.invoke(app, ["add", "buy milk"])
    assert result.exit_code == 0
    assert "Added" in _clean(result.output)
    assert "buy milk" in _clean(result.output)
    assert "buy milk" in _ls()


def test_add_high_priority(todo_file):
    runner.invoke(app, ["add", "urgent thing", "-h"])
    assert "high" in _ls()


def test_add_medium_priority(todo_file):
    runner.invoke(app, ["add", "medium thing", "-m"])
    assert "med" in _ls()


def test_add_long_priority_flags(todo_file):
    runner.invoke(app, ["add", "h_task", "--high"])
    runner.invoke(app, ["add", "m_task", "--med"])
    runner.invoke(app, ["add", "l_task", "--low"])
    runner.invoke(app, ["add", "n_task", "--never"])
    out = _ls()
    assert "h_task" in out
    assert "m_task" in out
    assert "l_task" in out
    assert "n_task" in out


def test_add_with_due_date(todo_file):
    runner.invoke(app, ["add", "alpha", "--due", "2026-06-10"])
    assert "2026-06-10" in _ls()


def test_add_with_multiple_tags(todo_file):
    runner.invoke(app, ["add", "alpha", "--tag", "school", "--tag", "work"])
    out = _ls()
    assert "#school" in out
    assert "#work" in out


def test_add_never_priority_overrides_due(todo_file):
    runner.invoke(app, ["add", "later thing", "-n", "--due", "2026-06-10"])
    out = _ls(["--all"])
    assert "never" in out
    assert "2026-06-10" not in out


def test_add_rejects_multiple_priority_flags(todo_file):
    result = runner.invoke(app, ["add", "alpha", "-h", "-m"])
    assert result.exit_code != 0
    assert "priority" in _clean(result.output).lower()


def test_add_rejects_bad_due_date(todo_file):
    result = runner.invoke(app, ["add", "alpha", "--due", "not-a-date"])
    assert result.exit_code != 0
    assert "due date" in _clean(result.output).lower()


# ---------- ls ----------

def test_ls_empty_shows_no_tasks(todo_file):
    result = runner.invoke(app, ["ls"])
    assert result.exit_code == 0
    assert "No tasks" in _clean(result.output)


def test_ls_default_hides_done(todo_file):
    runner.invoke(app, ["add", "alpha"])
    runner.invoke(app, ["add", "beta"])
    runner.invoke(app, ["done", "2"])
    out = _ls()
    assert "alpha" in out
    assert "beta" not in out


def test_ls_all_includes_done(todo_file):
    runner.invoke(app, ["add", "alpha"])
    runner.invoke(app, ["add", "beta"])
    runner.invoke(app, ["done", "2"])
    out = _ls(["--all"])
    assert "alpha" in out
    assert "beta" in out


def test_ls_done_only(todo_file):
    runner.invoke(app, ["add", "alpha"])
    runner.invoke(app, ["add", "beta"])
    runner.invoke(app, ["done", "2"])
    out = _ls(["--done"])
    assert "alpha" not in out
    assert "beta" in out


def test_ls_filter_by_tag(todo_file):
    runner.invoke(app, ["add", "alpha", "--tag", "school"])
    runner.invoke(app, ["add", "beta", "--tag", "work"])
    out = _ls(["--tag", "school"])
    assert "alpha" in out
    assert "beta" not in out


def test_ls_filter_by_priority(todo_file):
    runner.invoke(app, ["add", "alpha", "-h"])
    runner.invoke(app, ["add", "beta", "-l"])
    out = _ls(["--priority", "high"])
    assert "alpha" in out
    assert "beta" not in out


def test_ls_group_by_tag_shows_each_tag_section(todo_file):
    runner.invoke(app, ["add", "alpha", "--tag", "school"])
    runner.invoke(app, ["add", "beta", "--tag", "work"])
    out = _ls(["--group-by-tag"])
    assert "#school" in out
    assert "#work" in out


def test_ls_group_by_tag_untagged_section(todo_file):
    runner.invoke(app, ["add", "alpha"])
    out = _ls(["--group-by-tag"])
    assert "untagged" in out


def test_ls_sort_order_due_first_then_priority(todo_file):
    # Dated tasks come before undated; within dated, sort by date ascending;
    # within same date (or undated), sort by priority high -> never.
    runner.invoke(app, ["add", "undated_low", "-l"])
    runner.invoke(app, ["add", "undated_high", "-h"])
    runner.invoke(app, ["add", "late_high", "-h", "--due", "2026-07-15"])
    runner.invoke(app, ["add", "early_low", "-l", "--due", "2026-06-10"])
    runner.invoke(app, ["add", "early_high", "-h", "--due", "2026-06-10"])
    out = _ls()
    order = [
        out.index("early_high"),
        out.index("early_low"),
        out.index("late_high"),
        out.index("undated_high"),
        out.index("undated_low"),
    ]
    assert order == sorted(order), f"unexpected order: {order}"


# ---------- done / undone ----------

def test_done_marks_task(todo_file):
    runner.invoke(app, ["add", "alpha"])
    result = runner.invoke(app, ["done", "1"])
    assert result.exit_code == 0
    assert "Done" in _clean(result.output)
    assert "alpha" not in _ls()
    assert "alpha" in _ls(["--all"])


def test_done_missing_id_fails(todo_file):
    result = runner.invoke(app, ["done", "999"])
    assert result.exit_code == 1
    assert "not found" in _clean(result.output)


def test_undone_reverses_done(todo_file):
    runner.invoke(app, ["add", "alpha"])
    runner.invoke(app, ["done", "1"])
    result = runner.invoke(app, ["undone", "1"])
    assert result.exit_code == 0
    assert "Reopened" in _clean(result.output)
    assert "alpha" in _ls()


def test_undone_missing_id_fails(todo_file):
    result = runner.invoke(app, ["undone", "999"])
    assert result.exit_code == 1


# ---------- edit ----------

def test_edit_text(todo_file):
    runner.invoke(app, ["add", "alpha"])
    runner.invoke(app, ["edit", "1", "--text", "renamed"])
    out = _ls()
    assert "renamed" in out
    assert "alpha" not in out


def test_edit_priority(todo_file):
    runner.invoke(app, ["add", "alpha"])
    runner.invoke(app, ["edit", "1", "-h"])
    assert "high" in _ls()


def test_edit_long_priority_flag(todo_file):
    runner.invoke(app, ["add", "alpha"])
    runner.invoke(app, ["edit", "1", "--high"])
    assert "high" in _ls()


def test_edit_clears_due_with_no_date(todo_file):
    runner.invoke(app, ["add", "alpha", "--due", "2026-06-10"])
    runner.invoke(app, ["edit", "1", "--no-date"])
    out = _ls()
    assert "2026-06-10" not in out


def test_edit_replaces_due(todo_file):
    runner.invoke(app, ["add", "alpha", "--due", "2026-06-10"])
    runner.invoke(app, ["edit", "1", "--due", "2026-07-15"])
    out = _ls()
    assert "2026-06-10" not in out
    assert "2026-07-15" in out


def test_edit_clears_tags_with_no_tags(todo_file):
    runner.invoke(app, ["add", "alpha", "--tag", "school"])
    runner.invoke(app, ["edit", "1", "--no-tags"])
    assert "#school" not in _ls()


def test_edit_due_and_no_date_are_mutex(todo_file):
    runner.invoke(app, ["add", "alpha"])
    result = runner.invoke(app, ["edit", "1", "--due", "2026-06-10", "--no-date"])
    assert result.exit_code != 0


def test_edit_tag_and_no_tags_are_mutex(todo_file):
    runner.invoke(app, ["add", "alpha"])
    result = runner.invoke(app, ["edit", "1", "--tag", "school", "--no-tags"])
    assert result.exit_code != 0


def test_edit_missing_id_fails(todo_file):
    result = runner.invoke(app, ["edit", "999", "--text", "x"])
    assert result.exit_code == 1


# ---------- rm ----------

def test_rm_with_yes_flag_skips_prompt(todo_file):
    runner.invoke(app, ["add", "alpha"])
    result = runner.invoke(app, ["rm", "1", "-y"])
    assert result.exit_code == 0
    assert "Deleted" in _clean(result.output)
    assert "alpha" not in _ls(["--all"])


def test_rm_prompt_yes_deletes(todo_file):
    runner.invoke(app, ["add", "alpha"])
    result = runner.invoke(app, ["rm", "1"], input="y\n")
    assert result.exit_code == 0
    assert "Deleted" in _clean(result.output)


def test_rm_prompt_no_aborts(todo_file):
    runner.invoke(app, ["add", "alpha"])
    result = runner.invoke(app, ["rm", "1"], input="n\n")
    assert result.exit_code == 0
    assert "Aborted" in _clean(result.output)
    assert "alpha" in _ls()


def test_rm_missing_id_fails(todo_file):
    result = runner.invoke(app, ["rm", "999", "-y"])
    assert result.exit_code == 1


# ---------- clear ----------

def test_clear_removes_only_done(todo_file):
    runner.invoke(app, ["add", "alpha"])
    runner.invoke(app, ["add", "beta"])
    runner.invoke(app, ["done", "1"])
    result = runner.invoke(app, ["clear", "-y"])
    assert result.exit_code == 0
    assert "Cleared" in _clean(result.output)
    out = _ls(["--all"])
    assert "alpha" not in out
    assert "beta" in out


def test_clear_empty_when_no_done(todo_file):
    runner.invoke(app, ["add", "alpha"])
    result = runner.invoke(app, ["clear"])
    assert result.exit_code == 0
    assert "No completed" in _clean(result.output)


def test_clear_prompt_no_aborts(todo_file):
    runner.invoke(app, ["add", "alpha"])
    runner.invoke(app, ["done", "1"])
    result = runner.invoke(app, ["clear"], input="n\n")
    assert result.exit_code == 0
    assert "Aborted" in _clean(result.output)
    assert "alpha" in _ls(["--all"])


# ---------- reset ----------

def test_reset_with_yes_flag_wipes_everything(todo_file):
    runner.invoke(app, ["add", "alpha"])
    runner.invoke(app, ["add", "beta"])
    runner.invoke(app, ["done", "1"])
    result = runner.invoke(app, ["reset", "-y"])
    assert result.exit_code == 0
    assert "Deleted all" in _clean(result.output)
    assert "No tasks" in _ls(["--all"])


def test_reset_prompt_yes_wipes(todo_file):
    runner.invoke(app, ["add", "alpha"])
    result = runner.invoke(app, ["reset"], input="y\n")
    assert result.exit_code == 0
    assert "Deleted all" in _clean(result.output)


def test_reset_prompt_no_aborts(todo_file):
    runner.invoke(app, ["add", "alpha"])
    result = runner.invoke(app, ["reset"], input="n\n")
    assert result.exit_code == 0
    assert "Aborted" in _clean(result.output)
    assert "alpha" in _ls()


def test_reset_empty(todo_file):
    result = runner.invoke(app, ["reset"])
    assert result.exit_code == 0
    assert "No tasks" in _clean(result.output)


# ---------- NLP inline extraction ----------

def test_add_nlp_cleans_text_and_sets_due(todo_file):
    runner.invoke(app, ["add", "dentist friday"])
    data = json.loads(todo_file.read_text())
    assert data[0]["text"] == "dentist"
    assert data[0]["due"] is not None


def test_add_nlp_raw_preserves_original(todo_file):
    runner.invoke(app, ["add", "dentist friday"])
    data = json.loads(todo_file.read_text())
    assert data[0]["raw"] == "dentist friday"
    assert data[0]["text"] == "dentist"


def test_add_explicit_due_overrides_nlp(todo_file):
    runner.invoke(app, ["add", "dentist friday", "--due", "2026-07-01"])
    data = json.loads(todo_file.read_text())
    assert data[0]["due"] == "2026-07-01"
    assert data[0]["text"] == "dentist friday"  # no NLP stripping when --due given


def test_add_never_priority_skips_nlp(todo_file):
    runner.invoke(app, ["add", "dentist friday", "-n"])
    data = json.loads(todo_file.read_text())
    assert data[0]["due"] is None
    assert data[0]["text"] == "dentist friday"  # no stripping when priority=never


def test_add_nlp_shows_extracted_due(todo_file):
    result = runner.invoke(app, ["add", "call mom tomorrow"])
    assert result.exit_code == 0
    assert "→ due" in _clean(result.output)


def test_add_no_nlp_match_no_due(todo_file):
    runner.invoke(app, ["add", "buy milk"])
    data = json.loads(todo_file.read_text())
    assert data[0]["due"] is None
    assert data[0]["text"] == "buy milk"
