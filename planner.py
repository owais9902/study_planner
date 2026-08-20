"""
planner.py
-----------
Defines the StudyPlanner class: the core manager that holds a list of
Task objects and provides operations on them (add, remove, update,
search, filter, sort, and generate reports).

Also handles data persistence to JSON and export to CSV.

Demonstrates:
- Modular programming (single-responsibility class)
- Lists & dictionaries as core data structures
- File handling (JSON read/write, CSV export)
- Exception handling
- Search / filter / sort
"""

import json
import csv
import os
from datetime import datetime, date, timedelta

from task import Task, DATE_FORMAT


class StudyPlanner:
    """Manages a collection of study Task objects and their persistence."""

    def __init__(self, data_file="data/tasks.json"):
        self.data_file = data_file
        self.tasks = []          # list[Task]
        self._next_id = 1
        self.load_from_file()

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def add_task(self, subject, duration, priority, due_date):
        """Create and store a new Task. Raises ValueError on bad input."""
        task = Task(
            task_id=self._next_id,
            subject=subject,
            duration=duration,
            priority=priority,
            due_date=due_date,
        )
        self.tasks.append(task)
        self._next_id += 1
        self.save_to_file()
        return task

    def get_task(self, task_id):
        """Return a Task by id, or None if not found."""
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    def update_task(self, task_id, **fields):
        """
        Update fields of an existing task.
        Accepted keys: subject, duration, priority, due_date, completed.
        Raises ValueError if task not found or new values are invalid.
        """
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"No task found with ID {task_id}.")

        # Build a temp dict merging existing + new values, then re-validate
        # by constructing a fresh Task (reuses validation logic, avoids
        # duplicating rules here).
        current = task.to_dict()
        current.update(fields)
        updated = Task.from_dict({**current, "task_id": task_id})
        self.tasks[self.tasks.index(task)] = updated
        self.save_to_file()
        return updated

    def delete_task(self, task_id):
        """Remove a task by id. Returns True if deleted, False if not found."""
        task = self.get_task(task_id)
        if task is None:
            return False
        self.tasks.remove(task)
        self.save_to_file()
        return True

    def mark_complete(self, task_id):
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"No task found with ID {task_id}.")
        task.mark_complete()
        self.save_to_file()
        return task

    # ------------------------------------------------------------------
    # Search / filter / sort
    # ------------------------------------------------------------------
    def search_by_subject(self, keyword):
        """Case-insensitive substring search on subject name."""
        keyword = keyword.strip().lower()
        return [t for t in self.tasks if keyword in t.subject.lower()]

    def filter_by_priority(self, priority):
        priority = priority.strip().capitalize()
        return [t for t in self.tasks if t.priority == priority]

    def filter_by_completion(self, completed=True):
        return [t for t in self.tasks if t.completed == completed]

    def filter_overdue(self):
        return [t for t in self.tasks if t.is_overdue()]

    def filter_by_date_range(self, start_date, end_date):
        """Return tasks whose due_date falls within [start_date, end_date] inclusive."""
        start = datetime.strptime(start_date, DATE_FORMAT).date()
        end = datetime.strptime(end_date, DATE_FORMAT).date()
        result = []
        for t in self.tasks:
            due = datetime.strptime(t.due_date, DATE_FORMAT).date()
            if start <= due <= end:
                result.append(t)
        return result

    def get_today_plan(self):
        return self.filter_by_date_range(
            date.today().strftime(DATE_FORMAT),
            date.today().strftime(DATE_FORMAT),
        )

    def get_week_plan(self):
        today = date.today()
        week_end = today + timedelta(days=6)
        return self.filter_by_date_range(
            today.strftime(DATE_FORMAT), week_end.strftime(DATE_FORMAT)
        )

    def sort_tasks(self, key="due_date", reverse=False):
        """
        Sort tasks by a given key.
        Supported keys: due_date, priority, duration, subject, completed.
        Priority sorts High -> Medium -> Low by default (severity order).
        """
        priority_rank = {"High": 0, "Medium": 1, "Low": 2}

        if key == "priority":
            return sorted(
                self.tasks, key=lambda t: priority_rank[t.priority], reverse=reverse
            )
        if key == "due_date":
            return sorted(
                self.tasks,
                key=lambda t: datetime.strptime(t.due_date, DATE_FORMAT),
                reverse=reverse,
            )
        if key in ("duration", "subject", "completed"):
            return sorted(self.tasks, key=lambda t: getattr(t, key), reverse=reverse)

        raise ValueError(
            "Sort key must be one of: due_date, priority, duration, subject, completed."
        )

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------
    def overdue_report(self):
        """Return overdue tasks sorted by how many days overdue (most overdue first)."""
        overdue = self.filter_overdue()
        return sorted(overdue, key=lambda t: t.days_until_due())

    def progress_summary(self):
        """Return a dict of overall completion statistics."""
        total = len(self.tasks)
        completed = len(self.filter_by_completion(True))
        pending = total - completed
        overdue = len(self.filter_overdue())
        total_minutes = sum(t.duration for t in self.tasks)
        completed_minutes = sum(t.duration for t in self.tasks if t.completed)
        pct = round((completed / total) * 100, 1) if total else 0.0
        return {
            "total_tasks": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "completion_percent": pct,
            "total_planned_minutes": total_minutes,
            "completed_minutes": completed_minutes,
        }

    # ------------------------------------------------------------------
    # Persistence: JSON (primary store)
    # ------------------------------------------------------------------
    def save_to_file(self):
        """Persist all tasks to the JSON data file."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            payload = {
                "next_id": self._next_id,
                "tasks": [t.to_dict() for t in self.tasks],
            }
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except OSError as e:
            raise IOError(f"Could not save data to {self.data_file}: {e}")

    def load_from_file(self):
        """Load tasks from the JSON data file, if it exists."""
        if not os.path.exists(self.data_file):
            self.tasks = []
            self._next_id = 1
            return

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.tasks = [Task.from_dict(d) for d in payload.get("tasks", [])]
            self._next_id = payload.get(
                "next_id", (max((t.task_id for t in self.tasks), default=0) + 1)
            )
        except (json.JSONDecodeError, OSError) as e:
            # Corrupt or unreadable file: start fresh rather than crash.
            print(f"Warning: could not read {self.data_file} ({e}). Starting with an empty planner.")
            self.tasks = []
            self._next_id = 1
        except (KeyError, ValueError) as e:
            print(f"Warning: data file contained invalid task data ({e}). Some entries may be skipped.")

    # ------------------------------------------------------------------
    # Export: CSV
    # ------------------------------------------------------------------
    def export_to_csv(self, csv_file="data/tasks_export.csv"):
        """Export all current tasks to a CSV file."""
        try:
            os.makedirs(os.path.dirname(csv_file), exist_ok=True)
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                fieldnames = ["task_id", "subject", "duration", "priority",
                              "due_date", "completed", "created_at"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for t in self.tasks:
                    writer.writerow(t.to_dict())
            return csv_file
        except OSError as e:
            raise IOError(f"Could not export CSV to {csv_file}: {e}")
