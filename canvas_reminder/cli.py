from __future__ import annotations

import argparse
from datetime import datetime, timezone
import sys

from .canvas_client import CanvasClient
from .config import load_settings
from .emailer import send_smtp_email
from .reminder import build_email, collect_unfinished_assignments, should_send_for_schedule


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m canvas_reminder")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Fetch unfinished Canvas assignments and email a reminder.")
    run_parser.add_argument("--ignore-schedule", action="store_true", help="Bypass the Sunday 18:00 schedule guard.")
    args = parser.parse_args(argv)

    if args.command == "run":
        try:
            return run(ignore_schedule=args.ignore_schedule)
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    parser.error("Unknown command")
    return 2


def run(*, ignore_schedule: bool = False) -> int:
    settings = load_settings(require_email=True)
    now = datetime.now(timezone.utc)
    if not ignore_schedule and not should_send_for_schedule(now, settings.timezone, force_run=settings.force_run):
        print(f"Skipping run: current time is outside Sunday 18:00 in {settings.timezone}.")
        return 0

    client = CanvasClient(settings.canvas_base_url, settings.canvas_api_token)
    reminders = collect_unfinished_assignments(
        client,
        lookahead_days=settings.lookahead_days,
        timezone_name=settings.timezone,
        log_summary=True,
    )
    subject, text_body, html_body = build_email(reminders, today=now)

    print(f"Found {len(reminders)} unfinished assignment(s).")
    print(text_body)

    if settings.dry_run:
        print("DRY_RUN=true, email was not sent.")
        return 0

    send_smtp_email(
        sender=settings.smtp_email,
        password=settings.smtp_password,
        recipient=settings.recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
    )
    print(f"Email sent to {settings.recipient_email}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
