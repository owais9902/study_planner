# Study Planner

A command-line Study Planner that helps students plan subjects/tasks with
duration, priority, and due dates — track completion, see daily/weekly
study plans, and get an overdue report.

## Problem Statement

Students juggling multiple subjects often lose track of what to study,
how long to spend on it, and what's overdue. A simple, persistent,
text-based tool that captures tasks with duration, priority, and due
dates — and can slice that data into daily/weekly plans and overdue
reports — solves this without the overhead of a full app or spreadsheet.

## Objective

Build a functional Python CLI application that lets a user:

- Plan subjects/tasks with **duration, priority, due date, and completion
  status**.
- View a **daily or weekly study plan**.
- View a **schedule + overdue report**.
- Persist data between runs (no data lost on exit).

## Features

| # | Feature | Description |
|---|---------|--------------|
| 1 | Add a task | Subject, duration (min), priority (High/Medium/Low), due date |
| 2 | View all tasks | Lists every task with live status (Pending/Done/OVERDUE) |
| 3 | Update a task | Edit any field; blank input keeps the current value |
| 4 | Delete a task | Remove a task by ID |
| 5 | Mark complete | Marks a task done (also clears its overdue flag) |
| 6 | Search by subject | Case-insensitive substring search |
| 7 | Filter tasks | By priority, completed, pending, or overdue |
| 8 | Sort tasks | By due date, priority, duration, subject, or completion |
| 9 | Today's study plan | All tasks due today |
| 10 | This week's study plan | All tasks due in the next 7 days |
| 11 | Overdue report | Incomplete tasks past their due date, most-overdue first |
| 12 | Progress summary | Totals, completion %, minutes planned vs. completed |
| 13 | Export to CSV | Snapshot of all tasks as a `.csv` file |

Data is saved automatically to `data/tasks.json` after every change, so
closing and reopening the app preserves everything.

## Technologies Used

- **Python 3** (standard library only — no third-party runtime dependencies)
- `json` — data persistence
- `csv` — data export
- `datetime` — due-date and overdue calculations
- `unittest` — automated testing

## Installation / Setup Instructions

1. Make sure Python 3.8+ is installed:
   ```bash
   python3 --version
   ```
2. Copy the `study_planner/` project folder to your machine — no `pip
   install` is required, as the project only uses the Python standard
   library.

## How to Run the Project

From inside the `study_planner/` folder:

```bash
python3 main.py
```

You'll see a numbered menu. Enter a number and follow the prompts. Choose
`0` to exit (your data is already saved by then — every change is written
to disk immediately).

### Example: adding a task

```
Choose an option: 1

-- Add New Task --
Subject/Task name: Python Functions
Duration in minutes: 90
Priority (High/Medium/Low): High
Due date (YYYY-MM-DD): 2026-08-20
  Added: [1] Python Functions | 90 min | High priority | due 2026-08-20 | Pending
```

## Web Version (Optional)

The same underlying `Task`/`StudyPlanner` logic is also available as a
local web app (`app.py`), built with Flask, so you can use the planner
in your browser instead of the terminal.

### Install the one extra dependency

```bash
pip install -r requirements.txt
```

(This is the **only** part of the project that needs an external
package — the CLI version in `main.py` still needs nothing beyond the
standard library.)

### Run it

```bash
python3 app.py
```

Then open your browser to:

```
http://127.0.0.1:5000
```

You'll get a dashboard with the same features as the CLI: add/edit/
delete tasks, mark complete, search/filter/sort, today's plan, this
week's plan, an overdue report, and a CSV export button. Press
`Ctrl+C` in the terminal to stop the server.

## Project Structure

```
study_planner/
├── main.py                # CLI entry point / menu loop
├── app.py                 # Flask web front end (optional, reuses task.py/planner.py)
├── task.py                # Task class (model + validation)
├── planner.py              # StudyPlanner class (business logic + persistence)
├── templates/               # HTML templates used by app.py
│   ├── base.html
│   ├── index.html
│   ├── add_edit.html
│   ├── report.html
│   └── overdue.html
├── requirements.txt         # Only needed for the web version (Flask)
├── data/
│   ├── tasks.json          # Auto-created data store (persists between runs)
│   └── tasks_export.csv    # Created when the user exports to CSV
├── tests/
│   └── test_planner.py     # 30 automated unit tests
├── screenshots/             # Demonstration evidence (PNG)
├── docs/
│   └── project_report.md    # Project report
└── README.md
```

### Design overview

- **`task.py`** — a single `Task` class. All field validation (empty
  subject, non-numeric/negative/too-large duration, invalid priority,
  bad date format) lives here, so a `Task` object is *never* in an
  invalid state once constructed. Includes `is_overdue()`,
  `days_until_due()`, and `to_dict()`/`from_dict()` for JSON round-trips.
- **`planner.py`** — a single `StudyPlanner` class owning a `list[Task]`.
  Handles CRUD, search/filter/sort, reports, and file I/O (JSON load/save,
  CSV export). Keeping this separate from the CLI means the same class
  could back a GUI or web app later without changes.
- **`main.py`** — a thin CLI layer. It collects raw input, calls into
  `StudyPlanner`, and catches `ValueError`/`IOError` from bad input or
  file problems so the app never crashes on a bad entry.

## Testing Details

Run the full automated test suite from the project root:

```bash
python3 -m unittest discover -s tests -v
```

**30 tests, all passing**, organized into 6 test classes:

| Test class | What it covers |
|---|---|
| `TestTaskValidation` | Valid task creation, empty subject, zero/negative duration, duration upper boundary (1440 min), invalid priority, priority case-insensitivity, invalid date format |
| `TestOverdueLogic` | Past-due incomplete task is overdue; completed task is never overdue; future task is not overdue |
| `TestStudyPlannerCRUD` | Auto-incrementing IDs, duplicate subjects allowed as separate tasks, updating a missing ID raises, delete removes/returns correctly, mark-complete updates status |
| `TestSearchFilterSort` | Case-insensitive search, empty search results, filter by priority/completion, sort by priority and due date, invalid sort key raises |
| `TestPersistence` | Missing data file starts empty, data persists across instances, corrupt JSON is handled gracefully (no crash), CSV export creates a file |
| `TestProgressSummaryAndOverdueReport` | Empty-planner summary (no divide-by-zero), correct completion percentage, overdue report ordered most-overdue-first |

This deliberately covers **normal inputs, invalid inputs, boundary
conditions, duplicate data, and missing/corrupt data** as required.

See `docs/project_report.md` for a written summary of testing performed
and issues found along the way.

## Limitations

- Single-user, local file storage only — no multi-user accounts or sync.
- CLI only; no graphical interface.
- No recurring tasks (e.g. "study every Monday") — each task is a
  one-off entry.
- Due dates are date-only (no specific time of day).
- No undo for delete — deleting a task is immediate and permanent.

## Future Improvements

- A simple GUI (e.g. Tkinter) or web front end reusing the same
  `StudyPlanner`/`Task` classes unchanged.
- Recurring/repeating tasks and reminder notifications.
- Subject-level grouping and per-subject time totals/analytics.
- Priority-aware auto-scheduling ("what should I study next?").
- Multi-user support with separate data files or a real database.
