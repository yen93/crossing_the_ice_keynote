"""Loads environment variables and project_vars.txt constants for the pipeline."""

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TOKEN_STORE_PATH = BASE_DIR / ".google_token.json"

_FOLDER_ID_RE = re.compile(r"/folders/([a-zA-Z0-9_-]+)")


def _folder_id_from_link(link: str) -> str:
    match = _FOLDER_ID_RE.search(link)
    if not match:
        raise ValueError(f"Could not extract a Drive folder ID from: {link}")
    return match.group(1)


def _load_project_vars() -> dict:
    with open(BASE_DIR / "project_vars.txt", encoding="utf-8") as f:
        data = json.load(f)
    return data[0]


_PROJECT_VARS = _load_project_vars()

DEMO_NOTES_RECIPIENTS = _PROJECT_VARS["demo_notes_recipients"]
NOTIFICATION_RECIPIENTS = _PROJECT_VARS["notification_recipients"]
PROJ_DRIVE_FOLDER_ID = _folder_id_from_link(_PROJECT_VARS["proj_drive_link"])
TEMPLATES_DRIVE_FOLDER_ID = _folder_id_from_link(_PROJECT_VARS["templates_drive_link"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Optional: logo.dev publishable token. When set, the client-logo step tries a
# real brand logo from logo.dev before falling back to a Google favicon. When
# unset, only the (keyless) favicon is used. See logo_service.py.
LOGODEV_TOKEN = os.environ.get("LOGODEV_TOKEN", "")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Distinct from Uncharted Ice's and Interactive Keynote's trigger queries so
# all three can share one inbox without cross-triggering. This default is a
# best guess at the real inbound pattern for Crossing the Ice Keynote demo-
# call notes and should be tuned once real traffic is observed — see
# AS_BUILT_crossing_the_ice_keynote_automation.txt "Known limitations".
GMAIL_TRIGGER_QUERY = os.environ.get(
    "GMAIL_TRIGGER_QUERY",
    'has:attachment subject:("Crossing the Ice Keynote demo notes" OR "Crossing the Ice Keynote proposal")',
)

FATHOM_API_KEY = os.environ.get("FATHOM_API_KEY", "")
FATHOM_LOOKBACK_DAYS = int(os.environ.get("FATHOM_LOOKBACK_DAYS", "30"))

SUPABASE_LOG_TABLE = "crossing_the_ice_keynote_proposal_logs"

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/presentations",
]

REQUIRED_OCR_FIELDS = [
    "client_org",
    "summary",
]


def require(*names: str) -> None:
    """Raise a clear error if any of the named config values are unset."""
    missing = [n for n in names if not globals().get(n)]
    if missing:
        raise RuntimeError(
            f"Missing required configuration: {', '.join(missing)}. "
            f"Set them in {BASE_DIR / '.env'} (see .env.example)."
        )
