from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from html import escape
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from .canvas_client import extract_canvas_id


class CanvasDataSource(Protocol):
    def get_todo_items(self) -> list[dict[str, Any]]:
        ...

    def get_submission(self, course_id: int | str, assignment_id: int | str) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class AssignmentReminder:
    course_id: str
    course_name: str
    assignment_id: str
    assignment_name: str
    due_at: datetime
    html_url: str
    status: str
    overdue: bool


def collect_unfinished_assignments(
    client: CanvasDataSource,
    *,
    lookahead_days: int,
    timezone_name: str,
    now: datetime | None = None,
) -> list[AssignmentReminder]:
    timezone = ZoneInfo(timezone_name)
    now = now.astimezone(timezone) if now else datetime.now(timezone)
    lookahead_end = now + timedelta(days=lookahead_days)

    reminders: list[AssignmentReminder] = []
    for todo in client.get_todo_items():
        assignment = todo.get("assignment") or {}
        course = todo.get("course") or {}
        if not is_submission_required(assignment):
            continue
        due_at = parse_datetime(assignment.get("due_at"), timezone)
        if not due_at or due_at > lookahead_end:
            continue

        course_id = str(course.get("id") or assignment.get("course_id") or todo.get("course_id") or "")
        assignment_id = str(assignment.get("id") or todo.get("assignment_id") or extract_canvas_id(todo.get("html_url")) or "")
        if not course_id or not assignment_id:
            continue

        submission = client.get_submission(course_id, assignment_id)
        if is_finished(submission):
            continue

        html_url = assignment.get("html_url") or todo.get("html_url") or ""
        reminders.append(
            AssignmentReminder(
                course_id=course_id,
                course_name=str(course.get("name") or assignment.get("course_name") or "Unknown course"),
                assignment_id=assignment_id,
                assignment_name=str(assignment.get("name") or todo.get("title") or "Untitled assignment"),
                due_at=due_at,
                html_url=html_url,
                status=submission_status(submission, due_at, now),
                overdue=due_at < now,
            )
        )

    return sorted(reminders, key=lambda item: (item.due_at, item.course_name.lower(), item.assignment_name.lower()))


def parse_datetime(value: str | None, timezone: ZoneInfo) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone)
    return parsed.astimezone(timezone)


def is_finished(submission: dict[str, Any]) -> bool:
    workflow_state = str(submission.get("workflow_state") or "").lower()
    if workflow_state in {"submitted", "graded"}:
        return True
    if submission.get("submitted_at"):
        return True
    if submission.get("grade") is not None or submission.get("score") is not None:
        return True
    return False


def is_submission_required(assignment: dict[str, Any]) -> bool:
    submission_types = assignment.get("submission_types")
    if not submission_types:
        return True
    ignored_types = {"none", "not_graded"}
    return any(str(item).lower() not in ignored_types for item in submission_types)


def submission_status(submission: dict[str, Any], due_at: datetime, now: datetime) -> str:
    if due_at < now:
        return "OVERDUE"
    workflow_state = str(submission.get("workflow_state") or "").lower()
    if workflow_state == "unsubmitted":
        return "未提交"
    if workflow_state:
        return workflow_state
    return "待完成"


def build_email(reminders: list[AssignmentReminder], *, today: datetime) -> tuple[str, str, str]:
    subject = f"Canvas 未完成作业提醒 - {today.date().isoformat()}"
    if not reminders:
        text = "本周期没有待完成作业。"
        html = "<p>本周期没有待完成作业。</p>"
        return subject, text, html

    text_lines = ["以下是 Canvas 上未完成的作业：", ""]
    html_parts = [
        "<p>以下是 Canvas 上未完成的作业：</p>",
        "<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">",
        "<thead><tr><th>状态</th><th>截止时间</th><th>课程</th><th>作业</th><th>链接</th></tr></thead>",
        "<tbody>",
    ]

    for item in reminders:
        due_text = item.due_at.strftime("%Y-%m-%d %H:%M %Z")
        prefix = "[OVERDUE] " if item.overdue else ""
        text_lines.append(f"{prefix}{due_text} | {item.course_name} | {item.assignment_name} | {item.html_url}")
        html_parts.append(
            "<tr>"
            f"<td>{escape(item.status)}</td>"
            f"<td>{escape(due_text)}</td>"
            f"<td>{escape(item.course_name)}</td>"
            f"<td>{escape(item.assignment_name)}</td>"
            f"<td><a href=\"{escape(item.html_url, quote=True)}\">Open</a></td>"
            "</tr>"
        )

    html_parts.extend(["</tbody>", "</table>"])
    return subject, "\n".join(text_lines), "\n".join(html_parts)


def should_send_for_schedule(now: datetime, timezone_name: str, *, force_run: bool = False) -> bool:
    if force_run:
        return True
    local_now = now.astimezone(ZoneInfo(timezone_name))
    return local_now.weekday() == 6 and local_now.hour == 18
