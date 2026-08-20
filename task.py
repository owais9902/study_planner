"""
task.py
--------
Defines the Task class, which represents a single study task/subject entry
in the Study Planner application.

Demonstrates:
- Object-oriented programming (class, encapsulation, methods)
- Input validation (raises ValueError on bad data)
- Data structures (dict conversion for JSON persistence)
"""

from datetime import datetime, date


VALID_PRIORITIES = ("High", "Medium", "Low")
DATE_FORMAT = "%Y-%m-%d"


class Task:
    """
    Represents a single study task.

    Attributes:
        task_id (int): Unique identifier for the task.
        subject (str): Subject or topic name (e.g. "Python Functions").
        duration (int): Planned study duration in minutes.
        priority (str): One of "High", "Medium", "Low".
        due_date (str): Due date in YYYY-MM-DD format.
        completed (bool): Whether the task has been completed.
        created_at (str): Timestamp the task was created.
    """

    def __init__(self, task_id, subject, duration, priority, due_date,
                 completed=False, created_at=None):
        self.task_id = task_id
        self.subject = self._validate_subject(subject)
        self.duration = self._validate_duration(duration)
        self.priority = self._validate_priority(priority)
        self.due_date = self._validate_date(due_date)
        self.completed = bool(completed)
        self.created_at = created_at or datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------------
    # Validation helpers (static-style, but kept as instance methods so
    # subclasses could override behaviour if the project grew).
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_subject(subject):
        if not isinstance(subject, str) or not subject.strip():
            raise ValueError("Subject/task name cannot be empty.")
        return subject.strip()

    @staticmethod
    def _validate_duration(duration):
        try:
            duration = int(duration)
        except (TypeError, ValueError):
            raise ValueError("Duration must be a whole number of minutes.")
        if duration <= 0:
            raise ValueError("Duration must be greater than 0 minutes.")
        if duration > 1440:
            raise ValueError("Duration cannot exceed 1440 minutes (24 hours).")
        return duration

    @staticmethod
    def _validate_priority(priority):
        if not isinstance(priority, str):
            raise ValueError("Priority must be text.")
        priority = priority.strip().capitalize()
        if priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Priority must be one of {', '.join(VALID_PRIORITIES)}."
            )
        return priority

    @staticmethod
    def _validate_date(due_date):
        if isinstance(due_date, date) and not isinstance(due_date, datetime):
            return due_date.strftime(DATE_FORMAT)
        if not isinstance(due_date, str):
            raise ValueError("Due date must be a string in YYYY-MM-DD format.")
        try:
            datetime.strptime(due_date.strip(), DATE_FORMAT)
        except ValueError:
            raise ValueError("Due date must be in YYYY-MM-DD format (e.g. 2026-08-25).")
        return due_date.strip()

    # ------------------------------------------------------------------
    # Derived / computed properties
    # ------------------------------------------------------------------
    def is_overdue(self):
        """Return True if the task is not completed and due date has passed."""
        if self.completed:
            return False
        due = datetime.strptime(self.due_date, DATE_FORMAT).date()
        return due < date.today()

    def days_until_due(self):
        """Return number of days remaining until due date (negative if overdue)."""
        due = datetime.strptime(self.due_date, DATE_FORMAT).date()
        return (due - date.today()).days

    def mark_complete(self):
        self.completed = True

    def mark_incomplete(self):
        self.completed = False

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self):
        """Convert Task object to a dictionary (for JSON/CSV persistence)."""
        return {
            "task_id": self.task_id,
            "subject": self.subject,
            "duration": self.duration,
            "priority": self.priority,
            "due_date": self.due_date,
            "completed": self.completed,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Task object from a dictionary (loaded from JSON/CSV)."""
        return cls(
            task_id=data["task_id"],
            subject=data["subject"],
            duration=data["duration"],
            priority=data["priority"],
            due_date=data["due_date"],
            completed=data.get("completed", False),
            created_at=data.get("created_at"),
        )

    def __str__(self):
        status = "Done" if self.completed else ("OVERDUE" if self.is_overdue() else "Pending")
        return (f"[{self.task_id}] {self.subject} | {self.duration} min | "
                f"{self.priority} priority | due {self.due_date} | {status}")

    def __repr__(self):
        return f"Task({self.to_dict()!r})"
