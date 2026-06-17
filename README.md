# Canvas Reminder

Personal weekly Canvas unfinished assignment email reminders.

## Local Setup

1. Copy `.env.example` to `.env`.
2. Fill in your Canvas and SMTP email credentials.
3. Run a dry run:

```powershell
$env:DRY_RUN = "true"
python -m canvas_reminder run
```

4. Send a real email:

```powershell
$env:DRY_RUN = "false"
python -m canvas_reminder run
```

## Required Environment Variables

- `CANVAS_BASE_URL`: Canvas base URL, for example `https://your-school.instructure.com`
- `CANVAS_API_TOKEN`: Canvas API access token
- `SMTP_EMAIL`: SMTP sender email address, for example a Gmail address
- `SMTP_PASSWORD`: SMTP password, for example a Gmail app password
- `RECIPIENT_EMAIL`: destination email address

## Optional Environment Variables

- `SMTP_HOST`: defaults to `smtp.gmail.com`
- `SMTP_PORT`: defaults to `587`
- `LOOKAHEAD_DAYS`: defaults to `14`
- `TIMEZONE`: defaults to `Australia/Sydney`
- `DRY_RUN`: defaults to `false`
- `FORCE_RUN`: set to `true` to bypass the Sunday 18:00 schedule guard in GitHub Actions

## GitHub Actions

Add the required variables as GitHub repository secrets, then use the `Weekly Canvas Reminder` workflow. It runs on both UTC 07:00 and 08:00 every Sunday; the script checks `Australia/Sydney` locally so daylight saving time is handled correctly.
