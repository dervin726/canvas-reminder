from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    canvas_base_url: str
    canvas_api_token: str
    smtp_email: str
    smtp_password: str
    recipient_email: str
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    lookahead_days: int = 14
    timezone: str = "Australia/Sydney"
    dry_run: bool = False
    force_run: bool = False


def load_settings(require_email: bool = True) -> Settings:
    load_dotenv()

    required = ["CANVAS_BASE_URL", "CANVAS_API_TOKEN"]
    if require_email:
        required.extend(["SMTP_EMAIL", "SMTP_PASSWORD", "RECIPIENT_EMAIL"])

    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return Settings(
        canvas_base_url=os.environ["CANVAS_BASE_URL"].rstrip("/"),
        canvas_api_token=os.environ["CANVAS_API_TOKEN"],
        smtp_email=os.getenv("SMTP_EMAIL", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        recipient_email=os.getenv("RECIPIENT_EMAIL", ""),
        smtp_host=os.getenv("SMTP_HOST") or "smtp.gmail.com",
        smtp_port=int(os.getenv("SMTP_PORT") or "587"),
        lookahead_days=int(os.getenv("LOOKAHEAD_DAYS", "14")),
        timezone=os.getenv("TIMEZONE", "Australia/Sydney"),
        dry_run=env_bool("DRY_RUN", False),
        force_run=env_bool("FORCE_RUN", False),
    )
