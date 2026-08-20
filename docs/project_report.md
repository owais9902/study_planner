# Project Report — Study Planner

## 1. Problem Understanding

Students need a lightweight way to plan study tasks by subject, with a
duration estimate, a priority level, and a due date — and to be able to
see, at a glance, what to study today, what's due this week, and what
has slipped past its deadline. The requirement explicitly calls for a
**schedule + overdue report**, so overdue detection needed to be a
first-class, reliably tested feature rather than an afterthought.

The brief also specifies core Python concepts to demonstrate (functions,
data structures, conditionals/loops, input validation, exception
handling, file/JSON handling, OOP, search/filter/sort, persistence,
clean code) — so the design goal was not just "make it work" but "make
each of those concepts show up naturally, in the place it best belongs."

## 2. Proposed Approach

Three-layer separation, each with one job:

1. **`Task` (model / OOP)** — represents one task and guarantees it's
   always valid. All validation rules live here exactly once.
2. **`StudyPlanner` (business logic + persistence)** — owns the
   collection of tasks and every operation on it: add/update/delete,
   search, filter, sort, reports, JSON save/load, CSV export.
3. **`main.py` (CLI)** — a thin menu loop that only handles user I/O and
   delegates everything else to the two classes above.

This mirrors a typical real-world layering (model / service / UI) and
means the core logic is fully testable without any interactive input —
which is exactly how the 30-test suite works.

## 3. Implementation

- **Data structures:** each `Task` is an object; the planner holds them
  in a `list`; dictionaries are used for JSON/CSV round-tripping
  (`to_dict()` / `from_dict()`) and for the progress-summary report.
- **Conditional logic & loops:** the CLI menu loop, validation branching
  in `Task`, and the `for`/list-comprehension based filter and search
  methods in `StudyPlanner`.
- **Input validation:** centralized in `Task`'s private `_validate_*`
  static methods — duration must be a positive integer ≤ 1440, priority
  must be one of High/Medium/Low (case-normalized), and due date must
  parse as `YYYY-MM-DD`. The CLI layer adds a second layer (e.g.
  re-prompting on a blank subject) but always defers the actual rule to
  `Task`.
- **Exception handling:** `Task` raises `ValueError` for bad data;
  `StudyPlanner` raises `ValueError` for missing task IDs and `IOError`
  for file problems; `main.py` catches these at the point of use so one
  bad entry never crashes the session. `planner.py` also catches
  `json.JSONDecodeError`/`OSError` when loading, so a corrupted data file
  degrades to "start empty" instead of crashing on launch.
- **File handling / JSON / CSV:** `StudyPlanner.save_to_file()` /
  `load_from_file()` handle JSON persistence (auto-run after every
  mutating operation); `export_to_csv()` uses `csv.DictWriter` for a
  portable snapshot.
- **OOP:** `Task` and `StudyPlanner` are the two classes; `Task` uses
  `@staticmethod` validators, `@classmethod from_dict`, and dunder
  methods (`__str__`, `__repr__`) for readable output and debugging.
- **Search / filter / sort:** `search_by_subject()` (substring,
  case-insensitive), `filter_by_priority/completion/overdue()`,
  `sort_tasks()` (supports `due_date`, `priority` with a custom
  High→Medium→Low ranking, `duration`, `subject`, `completed`).
- **Persistence:** every mutating call (`add_task`, `update_task`,
  `delete_task`, `mark_complete`) immediately calls `save_to_file()`, so
  there's no separate "save" step for the user to remember.

## 4. Important Technical Decisions

- **Validate once, in the model.** Rather than validating in the CLI
  and again in the planner, all validation rules live in `Task`'s
  constructor. `StudyPlanner.update_task()` reuses this by rebuilding a
  `Task` from the merged old+new field dict — one rule set, no drift.
- **Priority as a fixed 3-value enum-like string** (`High`/`Medium`/`Low`)
  rather than a free-text field or numeric scale, so sorting and
  filtering stay simple and the CLI prompt stays unambiguous.
- **Save-on-every-write instead of an explicit "save" menu option.**
  Trades a little I/O overhead (irrelevant at this scale) for a
  guarantee that the user can never lose work by forgetting to save or
  by force-closing the terminal.
- **Corrupt/missing data files fail soft, not hard.** A missing
  `tasks.json` on first run, or an unreadable/corrupted one, results in
  an empty planner and a printed warning — not a crash — because a
  planning tool that refuses to start over a bad file is worse than one
  that quietly starts fresh.
- **`update_task` rebuilds via `Task.from_dict` instead of mutating
  fields in place**, so a partial update can never leave a `Task` in a
  state that skipped validation.

## 5. Testing Performed

30 automated `unittest` cases across 6 test classes (see `README.md` for
the full table), covering:

- **Normal inputs** — valid task creation, correct sort/filter/search
  results, correct progress-summary math.
- **Invalid inputs** — empty subject, non-numeric/negative duration,
  invalid priority, malformed date.
- **Boundary conditions** — duration exactly at 0 (rejected) and exactly
  at the 1440-minute cap (accepted) vs. 1441 (rejected); empty-planner
  summary stats (no divide-by-zero); a task due exactly today.
- **Duplicate data** — two tasks with the identical subject are allowed
  and tracked as distinct entries with distinct IDs.
- **Missing/corrupt data** — updating/deleting a non-existent task ID
  raises a clear error; a missing `tasks.json` starts an empty planner;
  a corrupted JSON file is caught and handled instead of crashing the
  app on startup.

Manual testing was also performed by running the actual CLI through
representative end-to-end sessions (add → view → update → delete → mark
complete → search → filter → sort → today/week plan → overdue report →
progress summary → CSV export), captured as screenshots in
`screenshots/`. All 30 automated tests pass; the CLI sessions were run
directly against the real `main.py`, not mocked, so the screenshots
reflect actual application behavior.

## 6. Challenges Encountered & Solutions

- **Challenge:** deciding how strict duration validation should be
  (should 0 minutes be allowed? what about a 20-hour study block?).
  **Solution:** set an explicit, documented boundary (`0 <
  duration ≤ 1440`) and wrote boundary tests for both ends so the rule
  is unambiguous and verified rather than implicit.
- **Challenge:** avoiding duplicated validation logic between "add" and
  "update" flows, since both need the same rules.
  **Solution:** `update_task` merges the existing task's dict with the
  requested changes and reconstructs a fresh `Task` via `from_dict`,
  so both paths funnel through the exact same validators.
- **Challenge:** making "overdue" behave correctly across timezones/
  completed tasks without extra complexity.
  **Solution:** `is_overdue()` compares only calendar dates (`date`, not
  `datetime`) and explicitly returns `False` for any completed task,
  which is directly covered by `TestOverdueLogic`.
- **Challenge:** a corrupted or hand-edited `tasks.json` could crash the
  app on the very next launch. **Solution:** wrapped the load path in
  `try/except (json.JSONDecodeError, OSError)` and fell back to an
  empty, working planner with a warning, verified by
  `test_corrupt_json_file_handled_gracefully`.

## 7. Future Scope

- Add recurring tasks and due-time (not just due-date) granularity.
- Add a lightweight GUI or web UI on top of the existing `StudyPlanner`
  class without changing its public interface.
- Add subject-level analytics (total time per subject, streaks).
- Add priority-aware "what should I study next" auto-suggestions based
  on due date and remaining time.
