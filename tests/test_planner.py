"""
test_planner.py
-----------------
Unit tests for the Study Planner application (Task + StudyPlanner classes).

Run with:
    python -m unittest discover -s tests -v
(run from the project root, i.e. study_planner/)

Covers: normal inputs, invalid inputs, boundary conditions, duplicate
entries, missing/corrupt data files, and persistence round-trips.
"""

import os
import sys
import json
import unittest
from datetime import date, timedelta

# Allow importing task.py / planner.py from the project root when running
# this test file from the tests/ directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from task import Task
from planner import StudyPlanner


TEST_DATA_FILE = os.path.join(os.path.dirname(__file__), "test_tasks.json")


def tomorrow():
    return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")


def yesterday():
    return (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")


class TestTaskValidation(unittest.TestCase):
    """Test Case 1: Task-level input validation (normal + invalid + boundary)."""

    def test_valid_task_creation(self):
        """Normal input: a fully valid task should be created without error."""
        t = Task(1, "Python Functions", 90, "High", tomorrow())
        self.assertEqual(t.subject, "Python Functions")
        self.assertEqual(t.duration, 90)
        self.assertEqual(t.priority, "High")
        self.assertFalse(t.completed)

    def test_empty_subject_rejected(self):
        """Invalid input: blank subject must raise ValueError."""
        with self.assertRaises(ValueError):
            Task(1, "   ", 30, "Medium", tomorrow())

    def test_negative_and_zero_duration_rejected(self):
        """Boundary condition: duration must be strictly positive."""
        with self.assertRaises(ValueError):
            Task(1, "Study", 0, "Low", tomorrow())
        with self.assertRaises(ValueError):
            Task(1, "Study", -10, "Low", tomorrow())

    def test_duration_upper_boundary(self):
        """Boundary condition: duration at and beyond the 1440-minute cap."""
        t = Task(1, "Marathon session", 1440, "Low", tomorrow())
        self.assertEqual(t.duration, 1440)
        with self.assertRaises(ValueError):
            Task(1, "Too long", 1441, "Low", tomorrow())

    def test_invalid_priority_rejected(self):
        """Invalid input: priority outside High/Medium/Low must fail."""
        with self.assertRaises(ValueError):
            Task(1, "Study", 30, "Urgent", tomorrow())

    def test_priority_case_insensitivity(self):
        """Normal input variant: lowercase priority should be normalized."""
        t = Task(1, "Study", 30, "high", tomorrow())
        self.assertEqual(t.priority, "High")

    def test_invalid_date_format_rejected(self):
        """Invalid input: malformed date string must raise ValueError."""
        with self.assertRaises(ValueError):
            Task(1, "Study", 30, "Medium", "20-08-2026")
        with self.assertRaises(ValueError):
            Task(1, "Study", 30, "Medium", "2026-13-40")


class TestOverdueLogic(unittest.TestCase):
    """Test Case 2: Overdue detection logic."""

    def test_past_due_incomplete_task_is_overdue(self):
        t = Task(1, "Old reading", 30, "High", yesterday())
        self.assertTrue(t.is_overdue())

    def test_past_due_completed_task_not_overdue(self):
        """A completed task should never be reported overdue, even if past due."""
        t = Task(1, "Old reading", 30, "High", yesterday(), completed=True)
        self.assertFalse(t.is_overdue())

    def test_future_task_not_overdue(self):
        t = Task(1, "Future reading", 30, "High", tomorrow())
        self.assertFalse(t.is_overdue())


class TestStudyPlannerCRUD(unittest.TestCase):
    """Test Case 3: StudyPlanner add/update/delete/complete operations."""

    def setUp(self):
        self._cleanup()
        self.planner = StudyPlanner(data_file=TEST_DATA_FILE)

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        if os.path.exists(TEST_DATA_FILE):
            os.remove(TEST_DATA_FILE)

    def test_add_task_assigns_incrementing_ids(self):
        t1 = self.planner.add_task("Task A", 30, "High", tomorrow())
        t2 = self.planner.add_task("Task B", 45, "Low", tomorrow())
        self.assertEqual(t1.task_id, 1)
        self.assertEqual(t2.task_id, 2)

    def test_duplicate_subject_allowed_as_separate_entries(self):
        """Duplicate scenario: same subject added twice should create two distinct tasks."""
        t1 = self.planner.add_task("Chemistry", 30, "Medium", tomorrow())
        t2 = self.planner.add_task("Chemistry", 45, "High", tomorrow())
        self.assertNotEqual(t1.task_id, t2.task_id)
        self.assertEqual(len(self.planner.search_by_subject("Chemistry")), 2)

    def test_update_nonexistent_task_raises(self):
        """Missing-data scenario: updating a task ID that doesn't exist."""
        with self.assertRaises(ValueError):
            self.planner.update_task(999, subject="Ghost Task")

    def test_delete_task_removes_it(self):
        t1 = self.planner.add_task("Task A", 30, "High", tomorrow())
        result = self.planner.delete_task(t1.task_id)
        self.assertTrue(result)
        self.assertIsNone(self.planner.get_task(t1.task_id))

    def test_delete_nonexistent_task_returns_false(self):
        result = self.planner.delete_task(999)
        self.assertFalse(result)

    def test_mark_complete_updates_status(self):
        t1 = self.planner.add_task("Task A", 30, "High", tomorrow())
        self.planner.mark_complete(t1.task_id)
        updated = self.planner.get_task(t1.task_id)
        self.assertTrue(updated.completed)


class TestSearchFilterSort(unittest.TestCase):
    """Test Case 4: Search, filter, and sort operations."""

    def setUp(self):
        self._cleanup()
        self.planner = StudyPlanner(data_file=TEST_DATA_FILE)
        self.planner.add_task("Python Functions", 90, "High", "2026-08-20")
        self.planner.add_task("Data Structures", 60, "Medium", "2026-08-19")
        self.planner.add_task("Linear Algebra", 45, "Low", "2026-08-25")
        self.planner.mark_complete(2)

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        if os.path.exists(TEST_DATA_FILE):
            os.remove(TEST_DATA_FILE)

    def test_search_by_subject_case_insensitive(self):
        results = self.planner.search_by_subject("python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].subject, "Python Functions")

    def test_search_no_match_returns_empty_list(self):
        """Boundary/missing-data scenario: search term with no matches."""
        results = self.planner.search_by_subject("Nonexistent Topic")
        self.assertEqual(results, [])

    def test_filter_by_priority(self):
        results = self.planner.filter_by_priority("High")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].subject, "Python Functions")

    def test_filter_by_completion_status(self):
        completed = self.planner.filter_by_completion(True)
        pending = self.planner.filter_by_completion(False)
        self.assertEqual(len(completed), 1)
        self.assertEqual(len(pending), 2)

    def test_sort_by_priority_orders_high_first(self):
        results = self.planner.sort_tasks(key="priority")
        priorities = [t.priority for t in results]
        self.assertEqual(priorities, ["High", "Medium", "Low"])

    def test_sort_by_due_date_ascending(self):
        results = self.planner.sort_tasks(key="due_date")
        dates = [t.due_date for t in results]
        self.assertEqual(dates, sorted(dates))

    def test_sort_invalid_key_raises(self):
        with self.assertRaises(ValueError):
            self.planner.sort_tasks(key="not_a_real_field")


class TestPersistence(unittest.TestCase):
    """Test Case 5: JSON persistence, reload, and handling of missing/corrupt files."""

    def setUp(self):
        self._cleanup()

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        if os.path.exists(TEST_DATA_FILE):
            os.remove(TEST_DATA_FILE)

    def test_missing_file_starts_with_empty_planner(self):
        """Missing-data scenario: no data file yet should not raise, just start empty."""
        planner = StudyPlanner(data_file=TEST_DATA_FILE)
        self.assertEqual(planner.tasks, [])

    def test_data_persists_across_instances(self):
        planner1 = StudyPlanner(data_file=TEST_DATA_FILE)
        planner1.add_task("Persisted Task", 30, "Medium", tomorrow())

        planner2 = StudyPlanner(data_file=TEST_DATA_FILE)
        self.assertEqual(len(planner2.tasks), 1)
        self.assertEqual(planner2.tasks[0].subject, "Persisted Task")

    def test_corrupt_json_file_handled_gracefully(self):
        """Invalid/corrupt file scenario: malformed JSON should not crash the app."""
        with open(TEST_DATA_FILE, "w", encoding="utf-8") as f:
            f.write("{ this is not valid json ][")
        planner = StudyPlanner(data_file=TEST_DATA_FILE)
        self.assertEqual(planner.tasks, [])  # falls back to empty rather than crashing

    def test_csv_export_creates_file(self):
        planner = StudyPlanner(data_file=TEST_DATA_FILE)
        planner.add_task("Export Test", 30, "Low", tomorrow())
        csv_path = os.path.join(os.path.dirname(__file__), "test_export.csv")
        try:
            result_path = planner.export_to_csv(csv_path)
            self.assertTrue(os.path.exists(result_path))
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)


class TestProgressSummaryAndOverdueReport(unittest.TestCase):
    """Additional test: progress summary calculations and overdue report ordering."""

    def setUp(self):
        self._cleanup()
        self.planner = StudyPlanner(data_file=TEST_DATA_FILE)

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        if os.path.exists(TEST_DATA_FILE):
            os.remove(TEST_DATA_FILE)

    def test_progress_summary_on_empty_planner(self):
        """Boundary condition: summary stats on an empty planner shouldn't divide by zero."""
        summary = self.planner.progress_summary()
        self.assertEqual(summary["total_tasks"], 0)
        self.assertEqual(summary["completion_percent"], 0.0)

    def test_progress_summary_calculates_correctly(self):
        self.planner.add_task("A", 30, "High", tomorrow())
        self.planner.add_task("B", 30, "High", tomorrow())
        self.planner.mark_complete(1)
        summary = self.planner.progress_summary()
        self.assertEqual(summary["total_tasks"], 2)
        self.assertEqual(summary["completed"], 1)
        self.assertEqual(summary["completion_percent"], 50.0)

    def test_overdue_report_orders_most_overdue_first(self):
        five_days_ago = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
        one_day_ago = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.planner.add_task("Least overdue", 30, "Low", one_day_ago)
        self.planner.add_task("Most overdue", 30, "Low", five_days_ago)
        report = self.planner.overdue_report()
        self.assertEqual(report[0].subject, "Most overdue")
        self.assertEqual(report[1].subject, "Least overdue")


if __name__ == "__main__":
    unittest.main(verbosity=2)
