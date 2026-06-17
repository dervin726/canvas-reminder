from datetime import datetime
from zoneinfo import ZoneInfo

from canvas_reminder.reminder import (
    AssignmentReminder,
    build_email,
    collect_unfinished_assignments,
    should_send_for_schedule,
)


class FakeCanvas:
    def __init__(self, todos, submissions):
        self.todos = todos
        self.submissions = submissions

    def get_todo_items(self):
        return self.todos

    def get_submission(self, course_id, assignment_id):
        return self.submissions[(str(course_id), str(assignment_id))]


def test_collect_unfinished_assignments_filters_submitted_no_due_date_and_no_submission():
    todos = [
        {
            "course": {"id": 1, "name": "COMP101"},
            "assignment": {"id": 10, "name": "Essay", "due_at": "2026-06-20T09:00:00Z", "html_url": "https://canvas/a/10"},
        },
        {
            "course": {"id": 1, "name": "COMP101"},
            "assignment": {"id": 11, "name": "Submitted", "due_at": "2026-06-21T09:00:00Z", "html_url": "https://canvas/a/11"},
        },
        {
            "course": {"id": 1, "name": "COMP101"},
            "assignment": {"id": 12, "name": "No Due", "due_at": None, "html_url": "https://canvas/a/12"},
        },
        {
            "course": {"id": 1, "name": "COMP101"},
            "assignment": {
                "id": 13,
                "name": "Read Only",
                "due_at": "2026-06-22T09:00:00Z",
                "html_url": "https://canvas/a/13",
                "submission_types": ["none"],
            },
        },
    ]
    submissions = {
        ("1", "10"): {"workflow_state": "unsubmitted"},
        ("1", "11"): {"workflow_state": "submitted", "submitted_at": "2026-06-18T10:00:00Z"},
    }
    now = datetime(2026, 6, 17, 10, tzinfo=ZoneInfo("Australia/Sydney"))

    reminders = collect_unfinished_assignments(
        FakeCanvas(todos, submissions),
        lookahead_days=14,
        timezone_name="Australia/Sydney",
        now=now,
    )

    assert [item.assignment_name for item in reminders] == ["Essay"]


def test_collect_unfinished_assignments_marks_overdue_and_sorts():
    todos = [
        {
            "course": {"id": 1, "name": "Course B"},
            "assignment": {"id": 20, "name": "Later", "due_at": "2026-06-21T09:00:00Z", "html_url": "https://canvas/a/20"},
        },
        {
            "course": {"id": 2, "name": "Course A"},
            "assignment": {"id": 21, "name": "Late", "due_at": "2026-06-15T09:00:00Z", "html_url": "https://canvas/a/21"},
        },
    ]
    submissions = {
        ("1", "20"): {"workflow_state": "unsubmitted"},
        ("2", "21"): {"workflow_state": "unsubmitted"},
    }
    now = datetime(2026, 6, 17, 10, tzinfo=ZoneInfo("Australia/Sydney"))

    reminders = collect_unfinished_assignments(
        FakeCanvas(todos, submissions),
        lookahead_days=14,
        timezone_name="Australia/Sydney",
        now=now,
    )

    assert [item.assignment_name for item in reminders] == ["Late", "Later"]
    assert reminders[0].overdue is True
    assert reminders[0].status == "OVERDUE"


def test_build_email_empty_state():
    subject, text, html = build_email([], today=datetime(2026, 6, 17, tzinfo=ZoneInfo("Australia/Sydney")))

    assert subject == "Canvas 未完成作业提醒 - 2026-06-17"
    assert "没有待完成作业" in text
    assert "没有待完成作业" in html


def test_build_email_lists_assignments():
    due_at = datetime(2026, 6, 20, 19, tzinfo=ZoneInfo("Australia/Sydney"))
    item = AssignmentReminder(
        course_id="1",
        course_name="COMP101",
        assignment_id="10",
        assignment_name="Essay",
        due_at=due_at,
        html_url="https://canvas/a/10",
        status="未提交",
        overdue=False,
    )

    _, text, html = build_email([item], today=datetime(2026, 6, 17, tzinfo=ZoneInfo("Australia/Sydney")))

    assert "COMP101" in text
    assert "Essay" in text
    assert "https://canvas/a/10" in text
    assert "<table" in html


def test_should_send_for_schedule_accepts_sunday_18_sydney():
    now = datetime(2026, 6, 14, 8, tzinfo=ZoneInfo("UTC"))

    assert should_send_for_schedule(now, "Australia/Sydney") is True


def test_should_send_for_schedule_rejects_other_hours():
    now = datetime(2026, 6, 14, 7, tzinfo=ZoneInfo("UTC"))

    assert should_send_for_schedule(now, "Australia/Sydney") is False
