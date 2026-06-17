# Canvas Reminder

Personal weekly Canvas unfinished assignment email reminders.

## Local Setup

1. Copy `.env.example` to `.env`.
2. Fill in your Canvas and Outlook credentials.
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
- `OUTLOOK_EMAIL`: Outlook sender email address
- `OUTLOOK_PASSWORD`: Outlook password or app password
- `RECIPIENT_EMAIL`: destination email address

## Optional Environment Variables

- `LOOKAHEAD_DAYS`: defaults to `14`
- `TIMEZONE`: defaults to `Australia/Sydney`
- `DRY_RUN`: defaults to `false`
- `FORCE_RUN`: set to `true` to bypass the Sunday 18:00 schedule guard in GitHub Actions

## GitHub Actions

Add the required variables as GitHub repository secrets, then use the `Weekly Canvas Reminder` workflow. It runs on both UTC 07:00 and 08:00 every Sunday; the script checks `Australia/Sydney` locally so daylight saving time is handled correctly.
