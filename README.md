# todo — Smart CLI Todo List

A terminal-based todo list that understands natural language. Type tasks the
way you think them — "dentist friday" or "pay rent 1st of next month" — and
the due date is parsed automatically. Tasks are stored locally in JSON so the
tool works fully offline.

## Usage

Install dependencies and register the `todo` command:

```bash
brew install uv
uv sync
```

All subcommands are available as `todo <command>`. Run `todo --help` or
`todo <command> --help` for full flag details.

---

### `add` — Add a task

```
todo add "<text>" [OPTIONS]
```

| Flag | Description |
|---|---|
| `-h` / `--high` | High priority |
| `-m` / `--med` | Medium priority |
| `-l` / `--low` | Low priority (default) |
| `-n` / `--never` | Never priority — clears any due date |
| `--due <date>` | Explicit due date (ISO format, e.g. `2026-06-14`). Skips NLP parsing. |
| `--tag <tag>` | Tag for classification; repeat to apply multiple |

When `--due` is omitted, the task text is scanned for a natural language date
phrase (see [Pattern Matching](#pattern-matching) below).

---

### `ls` — List tasks

```
todo ls [OPTIONS]
```

| Flag | Description |
|---|---|
| `-a` / `--all` | Include completed tasks |
| `--done` | Show only completed tasks |
| `--tag <tag>` | Filter by tag |
| `--priority <level>` | Filter by priority (`never` / `low` / `med` / `high`) |
| `-g` / `--group-by-tag` | Render one table per tag |

Tasks are sorted: dated tasks first (ascending by date), then undated tasks by
priority (high → never).

---

### `done` / `undone` — Complete or reopen a task

```
todo done <id>
todo undone <id>
```

---

### `edit` — Modify a task

```
todo edit <id> [OPTIONS]
```

Only the flags you supply are changed. `--no-date` clears the due date;
`--no-tags` clears all tags. `--due` and `--no-date` are mutually exclusive,
as are `--tag` and `--no-tags`.

---

### `rm` — Delete a task

```
todo rm <id> [OPTIONS]
```

Prompts for confirmation unless `-y` / `--yes` is given.

---

### `clear` — Remove all completed tasks

```
todo clear [OPTIONS]
```

Pending tasks are not affected.

---

### `reset` — Wipe everything

```
todo reset [OPTIONS]
```

Deletes all tasks, completed and pending.

---

## Pattern Matching

When you add a task without `--due`, the tool scans the task text for a
recognizable date phrase, extracts it as the due date, and removes it from the
stored task name. The original input is always preserved in the `raw` field.

**Priority `-n/--never` skips NLP entirely** — the text is stored as typed
with no due date.

### Supported patterns

| Category | Examples | Resolves to |
|---|---|---|
| Today / tomorrow | `today`, `tod`, `tomorrow`, `tmr`, `tmrw` | today or today + 1 |
| Weekday names | `friday`, `fri`, `Friday`, `FRIDAY`, `fri.` | next occurrence of that day (never today) |
| Qualified weekday | `this friday`, `upcoming friday` | same as bare weekday |
| Next weekday | `next friday` | one week after the bare result |
| Relative offset | `in 2 days`, `3 weeks from now`, `a month from now` | today + offset |
| End of week | `end of week`, `eow` | coming Friday |
| End of month | `end of month`, `eom` | last day of current month |
| Next month | `next month` | first day of next month |
| Ordinal day | `14th`, `the 14th`, `on the 14th` | 14th of current month if not past, else next month |
| Ordinal + next month | `next month 14th`, `14th of next month`, `on the 14th of next month` | 14th of next month |
| First weekday of next month | `first friday of next month` | first matching weekday of next month |
| Named month + day | `june 14`, `jun 14th`, `june the 14th` | that date this year, or next year if past |
| Day + named month | `14th of june`, `14 june`, `3rd of jul` | same as above |

Month names and weekday names are **case-insensitive** and support common
**abbreviations** (`jan`, `feb`, `mar`, `apr`, `jun`, `jul`, `aug`, `sep`,
`sept`, `oct`, `nov`, `dec`).

---

## Example Usage

```bash
# Add a basic task (default low priority)
todo add "buy milk"

# Add with inline NLP date — due date is parsed from the text
todo add "dentist friday"
todo add "call mom tomorrow"
todo add "pay rent 1st of next month"
todo add "submit report in 3 days"
todo add "team standup this thursday"
todo add "review pr next monday"
todo add "birthday party june 14"
todo add "file taxes jan 31"

# Add with explicit due date (NLP is skipped)
todo add "project deadline" --due 2026-07-01

# Add with priority and tags
todo add "fix critical bug" --high --tag work
todo add "read book" --low --tag personal
todo add "someday maybe" --never

# List tasks
todo ls                        # active tasks only
todo ls --all                  # include completed
todo ls --done                 # only completed
todo ls --tag work             # filter by tag
todo ls --priority high        # filter by priority
todo ls --group-by-tag         # one table per tag

# Complete and reopen
todo done 3
todo undone 3

# Edit a task
todo edit 2 --text "updated description"
todo edit 2 --high --due 2026-07-15
todo edit 2 --no-date
todo edit 2 --tag school --tag urgent

# Delete a task
todo rm 4              # prompts for confirmation
todo rm 4 -y           # skip prompt

# Clean up
todo clear             # remove all completed tasks
todo clear -y          # skip prompt
todo reset -y          # wipe everything
```
