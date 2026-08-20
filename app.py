"""
app.py
-------
Flask web front end for the Study Planner.

Reuses the existing Task/StudyPlanner classes from task.py / planner.py
unchanged -- this file only adds routes (URLs) and renders HTML templates.
All validation, persistence, search/filter/sort, and reporting logic
still lives in planner.py / task.py.

Run with:
    python3 app.py
Then open:
    http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, redirect, url_for, flash

from planner import StudyPlanner

app = Flask(__name__)
app.secret_key = "study-planner-dev-key"  # only needed for flash messages

planner = StudyPlanner(data_file="data/tasks.json")


# ----------------------------------------------------------------------
# Dashboard / task list (with optional search, filter, sort via query params)
# ----------------------------------------------------------------------
@app.route("/")
def index():
    keyword = request.args.get("q", "").strip()
    priority = request.args.get("priority", "").strip()
    status = request.args.get("status", "").strip()
    sort_key = request.args.get("sort", "due_date").strip()
    order = request.args.get("order", "asc").strip()

    tasks = planner.tasks

    if keyword:
        tasks = [t for t in tasks if keyword.lower() in t.subject.lower()]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    if status == "completed":
        tasks = [t for t in tasks if t.completed]
    elif status == "pending":
        tasks = [t for t in tasks if not t.completed]
    elif status == "overdue":
        tasks = [t for t in tasks if t.is_overdue()]

    priority_rank = {"High": 0, "Medium": 1, "Low": 2}
    reverse = order == "desc"
    if sort_key == "priority":
        tasks = sorted(tasks, key=lambda t: priority_rank[t.priority], reverse=reverse)
    elif sort_key == "due_date":
        tasks = sorted(tasks, key=lambda t: t.due_date, reverse=reverse)
    elif sort_key in ("duration", "subject", "completed"):
        tasks = sorted(tasks, key=lambda t: getattr(t, sort_key), reverse=reverse)

    summary = planner.progress_summary()

    return render_template(
        "index.html",
        tasks=tasks,
        summary=summary,
        keyword=keyword,
        priority=priority,
        status=status,
        sort_key=sort_key,
        order=order,
    )


# ----------------------------------------------------------------------
# Add task
# ----------------------------------------------------------------------
@app.route("/add", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        subject = request.form.get("subject", "")
        duration = request.form.get("duration", "")
        priority = request.form.get("priority", "")
        due_date = request.form.get("due_date", "")
        try:
            planner.add_task(subject, duration, priority, due_date)
            flash(f'Added "{subject}" successfully.', "success")
            return redirect(url_for("index"))
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "add_edit.html", mode="add",
                subject=subject, duration=duration, priority=priority, due_date=due_date,
            )
    return render_template("add_edit.html", mode="add")


# ----------------------------------------------------------------------
# Edit task
# ----------------------------------------------------------------------
@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    task = planner.get_task(task_id)
    if task is None:
        flash(f"No task found with ID {task_id}.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        fields = {
            "subject": request.form.get("subject", ""),
            "duration": request.form.get("duration", ""),
            "priority": request.form.get("priority", ""),
            "due_date": request.form.get("due_date", ""),
        }
        try:
            planner.update_task(task_id, **fields)
            flash("Task updated successfully.", "success")
            return redirect(url_for("index"))
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "add_edit.html", mode="edit", task_id=task_id, **fields
            )

    return render_template(
        "add_edit.html", mode="edit", task_id=task_id,
        subject=task.subject, duration=task.duration,
        priority=task.priority, due_date=task.due_date,
    )


# ----------------------------------------------------------------------
# Delete task
# ----------------------------------------------------------------------
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    if planner.delete_task(task_id):
        flash(f"Task {task_id} deleted.", "success")
    else:
        flash(f"No task found with ID {task_id}.", "error")
    return redirect(url_for("index"))


# ----------------------------------------------------------------------
# Mark complete / incomplete (toggle)
# ----------------------------------------------------------------------
@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_complete(task_id):
    task = planner.get_task(task_id)
    if task is None:
        flash(f"No task found with ID {task_id}.", "error")
        return redirect(url_for("index"))
    if task.completed:
        planner.update_task(task_id, completed=False)
        flash(f'Marked "{task.subject}" as pending.', "success")
    else:
        planner.mark_complete(task_id)
        flash(f'Marked "{task.subject}" as complete.', "success")
    return redirect(url_for("index"))


# ----------------------------------------------------------------------
# Reports: today / week / overdue
# ----------------------------------------------------------------------
@app.route("/today")
def today_plan():
    return render_template(
        "report.html", title="Today's Study Plan", tasks=planner.get_today_plan()
    )


@app.route("/week")
def week_plan():
    return render_template(
        "report.html", title="This Week's Study Plan", tasks=planner.get_week_plan()
    )


@app.route("/overdue")
def overdue_report():
    return render_template(
        "overdue.html", title="Overdue Report", tasks=planner.overdue_report()
    )


# ----------------------------------------------------------------------
# CSV export (downloads the file)
# ----------------------------------------------------------------------
@app.route("/export")
def export_csv():
    from flask import send_file
    path = planner.export_to_csv("data/tasks_export.csv")
    return send_file(path, as_attachment=True, download_name="tasks_export.csv")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
