"""
main.py
--------
Command-line interface for the Study Planner application.

Run with:  python main.py

Demonstrates:
- Modular programming (delegates logic to Task/StudyPlanner)
- Conditional logic & loops (menu-driven interaction)
- Input validation & exception handling at the UI boundary
"""

from planner import StudyPlanner


MENU = """
==================== STUDY PLANNER ====================
 1. Add a new task
 2. View all tasks
 3. Update a task
 4. Delete a task
 5. Mark task as complete
 6. Search tasks by subject
 7. Filter tasks (priority / status / overdue)
 8. Sort tasks
 9. Today's study plan
10. This week's study plan
11. Overdue report
12. Progress summary
13. Export tasks to CSV
 0. Exit
=========================================================
"""


def prompt_nonempty(label):
    while True:
        value = input(label).strip()
        if value:
            return value
        print("  This field cannot be empty. Please try again.")


def prompt_int(label):
    while True:
        raw = input(label).strip()
        try:
            return int(raw)
        except ValueError:
            print("  Please enter a whole number.")


def print_tasks(tasks):
    if not tasks:
        print("  (no tasks to show)")
        return
    for t in tasks:
        print(f"  {t}")


def add_task_flow(planner):
    print("\n-- Add New Task --")
    subject = prompt_nonempty("Subject/Task name: ")
    duration_raw = input("Duration in minutes: ").strip()
    priority = input("Priority (High/Medium/Low): ").strip()
    due_date = input("Due date (YYYY-MM-DD): ").strip()
    try:
        task = planner.add_task(subject, duration_raw, priority, due_date)
        print(f"  Added: {task}")
    except ValueError as e:
        print(f"  Error: {e}")


def view_tasks_flow(planner):
    print("\n-- All Tasks --")
    print_tasks(planner.tasks)


def update_task_flow(planner):
    print("\n-- Update Task --")
    task_id = prompt_int("Task ID to update: ")
    task = planner.get_task(task_id)
    if task is None:
        print(f"  No task found with ID {task_id}.")
        return
    print(f"  Current: {task}")
    print("  Leave a field blank to keep its current value.")
    fields = {}
    subject = input(f"  New subject [{task.subject}]: ").strip()
    if subject:
        fields["subject"] = subject
    duration = input(f"  New duration in minutes [{task.duration}]: ").strip()
    if duration:
        fields["duration"] = duration
    priority = input(f"  New priority [{task.priority}]: ").strip()
    if priority:
        fields["priority"] = priority
    due_date = input(f"  New due date [{task.due_date}]: ").strip()
    if due_date:
        fields["due_date"] = due_date

    if not fields:
        print("  No changes made.")
        return

    try:
        updated = planner.update_task(task_id, **fields)
        print(f"  Updated: {updated}")
    except ValueError as e:
        print(f"  Error: {e}")


def delete_task_flow(planner):
    print("\n-- Delete Task --")
    task_id = prompt_int("Task ID to delete: ")
    if planner.delete_task(task_id):
        print(f"  Task {task_id} deleted.")
    else:
        print(f"  No task found with ID {task_id}.")


def complete_task_flow(planner):
    print("\n-- Mark Task Complete --")
    task_id = prompt_int("Task ID to mark complete: ")
    try:
        task = planner.mark_complete(task_id)
        print(f"  Marked complete: {task}")
    except ValueError as e:
        print(f"  Error: {e}")


def search_flow(planner):
    print("\n-- Search by Subject --")
    keyword = prompt_nonempty("Keyword: ")
    results = planner.search_by_subject(keyword)
    print(f"  {len(results)} match(es) found:")
    print_tasks(results)


def filter_flow(planner):
    print("\n-- Filter Tasks --")
    print("  1. By priority")
    print("  2. Completed tasks")
    print("  3. Pending tasks")
    print("  4. Overdue tasks")
    choice = input("  Choose an option: ").strip()

    if choice == "1":
        priority = input("  Priority (High/Medium/Low): ").strip()
        try:
            results = planner.filter_by_priority(priority)
        except Exception as e:
            print(f"  Error: {e}")
            return
    elif choice == "2":
        results = planner.filter_by_completion(True)
    elif choice == "3":
        results = planner.filter_by_completion(False)
    elif choice == "4":
        results = planner.filter_overdue()
    else:
        print("  Invalid option.")
        return

    print(f"  {len(results)} task(s) found:")
    print_tasks(results)


def sort_flow(planner):
    print("\n-- Sort Tasks --")
    print("  Keys: due_date, priority, duration, subject, completed")
    key = input("  Sort by: ").strip() or "due_date"
    order = input("  Order (asc/desc) [asc]: ").strip().lower() or "asc"
    try:
        results = planner.sort_tasks(key=key, reverse=(order == "desc"))
        print_tasks(results)
    except ValueError as e:
        print(f"  Error: {e}")


def today_plan_flow(planner):
    print("\n-- Today's Study Plan --")
    print_tasks(planner.get_today_plan())


def week_plan_flow(planner):
    print("\n-- This Week's Study Plan --")
    print_tasks(planner.get_week_plan())


def overdue_report_flow(planner):
    print("\n-- Overdue Report --")
    overdue = planner.overdue_report()
    if not overdue:
        print("  Nothing overdue. Great job staying on track!")
        return
    for t in overdue:
        days = abs(t.days_until_due())
        print(f"  {t}  -> {days} day(s) overdue")


def progress_summary_flow(planner):
    print("\n-- Progress Summary --")
    summary = planner.progress_summary()
    print(f"  Total tasks:        {summary['total_tasks']}")
    print(f"  Completed:          {summary['completed']}")
    print(f"  Pending:            {summary['pending']}")
    print(f"  Overdue:            {summary['overdue']}")
    print(f"  Completion rate:    {summary['completion_percent']}%")
    print(f"  Total planned time: {summary['total_planned_minutes']} min")
    print(f"  Completed time:     {summary['completed_minutes']} min")


def export_csv_flow(planner):
    print("\n-- Export to CSV --")
    path = input("  Output path [data/tasks_export.csv]: ").strip()
    path = path or "data/tasks_export.csv"
    try:
        saved_path = planner.export_to_csv(path)
        print(f"  Exported {len(planner.tasks)} task(s) to {saved_path}")
    except IOError as e:
        print(f"  Error: {e}")


def main():
    planner = StudyPlanner(data_file="data/tasks.json")

    actions = {
        "1": add_task_flow,
        "2": view_tasks_flow,
        "3": update_task_flow,
        "4": delete_task_flow,
        "5": complete_task_flow,
        "6": search_flow,
        "7": filter_flow,
        "8": sort_flow,
        "9": today_plan_flow,
        "10": week_plan_flow,
        "11": overdue_report_flow,
        "12": progress_summary_flow,
        "13": export_csv_flow,
    }

    print("Welcome to Study Planner!")

    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()

        if choice == "0":
            print("Goodbye! Keep up the good study habits.")
            break

        action = actions.get(choice)
        if action is None:
            print("Invalid option. Please choose a number from the menu.")
            continue

        try:
            action(planner)
        except Exception as e:
            # Safety net: unexpected errors shouldn't crash the whole app.
            print(f"  Unexpected error: {e}")


if __name__ == "__main__":
    main()
