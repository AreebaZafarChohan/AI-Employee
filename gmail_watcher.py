#!/usr/bin/env python3
"""Silver Tier Gmail Watcher.

Polls Gmail for unread important emails and creates markdown files in
AI-Employee-Vault/Needs_Action/ for the agent pipeline to process.

Usage:
    python gmail_watcher.py              # run one poll cycle then exit
    python gmail_watcher.py --watch      # poll on a schedule (POLL_INTERVAL_SECONDS)
    DRY_RUN=true python gmail_watcher.py # log actions without writing any files

Environment variables (all optional except Gmail OAuth credentials):
    VAULT_PATH               Path to AI-Employee vault (default: ./AI-Employee-Vault)
    GMAIL_CREDENTIALS_FILE   Path to OAuth2 client secrets JSON (default: credentials.json)
    GMAIL_TOKEN_FILE         Path to cached token (default: token.json)
    POLL_INTERVAL_SECONDS    Seconds between polls in --watch mode (default: 60)
    MAX_RESULTS              Max emails fetched per poll (default: 20)
    DRY_RUN                  Set to "true" to skip all writes (default: false)
    LOG_LEVEL                Logging verbosity DEBUG/INFO/WARNING/ERROR (default: INFO)

Gmail API scopes required:
    https://www.googleapis.com/auth/gmail.readonly
    https://www.googleapis.com/auth/gmail.modify   (for marking emails processed)

Setup:
    1. Enable Gmail API in Google Cloud Console.
    2. Download OAuth2 client secrets JSON → credentials.json
    3. pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
    4. Run once interactively to complete OAuth flow → token.json is cached.
"""

import argparse
import base64
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap: allow running from project root without installing the package
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.utils.logger import log_action, set_default_logs_dir  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_PATH = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
LOGS_DIR = VAULT_PATH / "Logs"

CREDENTIALS_FILE = Path(os.getenv("GMAIL_CREDENTIALS_FILE", ROOT / "credentials.json"))
TOKEN_FILE = Path(os.getenv("GMAIL_TOKEN_FILE", ROOT / "token.json"))
LEDGER_FILE = VAULT_PATH / ".gmail_processed.json"

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "20"))
DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")

# Retry settings
MAX_RETRIES = 4
RETRY_BASE_DELAY = 2.0   # seconds; doubled on each attempt

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _build_logger() -> logging.Logger:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger("gmail_watcher")
    if logger.handlers:
        return logger  # already configured (e.g. imported as module)

    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | gmail_watcher | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fh = logging.FileHandler(LOGS_DIR / f"gmail-watcher-{today}.log", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


logger = _build_logger()

# ---------------------------------------------------------------------------
# Ledger — persistent dedup guard (keyed by Gmail message ID)
# ---------------------------------------------------------------------------

def _load_ledger() -> set[str]:
    if not LEDGER_FILE.exists():
        return set()
    try:
        return set(json.loads(LEDGER_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load ledger, starting fresh: %s", exc)
        return set()


def _save_ledger(entries: set[str]) -> None:
    if DRY_RUN:
        return
    LEDGER_FILE.write_text(
        json.dumps(sorted(entries), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Gmail OAuth — build an authenticated service object
# ---------------------------------------------------------------------------

def _build_gmail_service() -> Any:
    """Authenticate and return a Gmail API service object.

    On the first run this opens a browser window for the OAuth consent screen.
    Subsequent runs load the cached token from TOKEN_FILE.
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        logger.error(
            "Gmail API dependencies missing. Install with:\n"
            "  pip install google-auth google-auth-oauthlib "
            "google-auth-httplib2 google-api-python-client\n"
            "Error: %s",
            exc,
        )
        raise SystemExit(1) from exc

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Gmail token…")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                logger.error(
                    "credentials.json not found at %s.\n"
                    "Download OAuth2 client secrets from Google Cloud Console.",
                    CREDENTIALS_FILE,
                )
                raise SystemExit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), GMAIL_SCOPES
            )
            # Manual console flow — works in WSL2/headless environments.
            # Print the auth URL, user opens it in browser, pastes code back.
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            auth_url, _ = flow.authorization_url(prompt="consent")
            print("\n" + "="*60)
            print("Open this URL in your browser:")
            print(auth_url)
            print("="*60)
            auth_code = input("Paste the authorization code here: ").strip()
            flow.fetch_token(code=auth_code)
            creds = flow.credentials

        if not DRY_RUN:
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            logger.info("Token saved to %s", TOKEN_FILE)

    return build("gmail", "v1", credentials=creds)


# ---------------------------------------------------------------------------
# Retry decorator with exponential backoff
# ---------------------------------------------------------------------------

def _with_retry(fn, *args, label: str = "operation", **kwargs) -> Any:
    """Call fn(*args, **kwargs) with exponential backoff on transient errors.

    Raises the final exception if all retries are exhausted.
    """
    delay = RETRY_BASE_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            if attempt == MAX_RETRIES:
                logger.error("%s failed after %d attempts: %s", label, MAX_RETRIES, exc)
                raise
            logger.warning(
                "%s attempt %d/%d failed (%s). Retrying in %.1fs…",
                label,
                attempt,
                MAX_RETRIES,
                exc,
                delay,
            )
            time.sleep(delay)
            delay *= 2


# ---------------------------------------------------------------------------
# Email fetching
# ---------------------------------------------------------------------------

def _fetch_unread_important(service: Any) -> list[dict]:
    """Return a list of raw Gmail message objects for unread important emails."""
    query = "is:unread (is:important OR is:starred)"
    response = _with_retry(
        service.users().messages().list(
            userId="me", q=query, maxResults=MAX_RESULTS
        ).execute,
        label="list_messages",
    )
    messages = response.get("messages", [])
    if not messages:
        return []

    full_messages = []
    for msg_stub in messages:
        full = _with_retry(
            service.users().messages().get(
                userId="me",
                id=msg_stub["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute,
            label=f"get_message:{msg_stub['id']}",
        )
        full_messages.append(full)

    return full_messages


# ---------------------------------------------------------------------------
# Email parsing
# ---------------------------------------------------------------------------

def _parse_priority(label_ids: list[str]) -> str:
    """Derive a human-readable priority from Gmail label IDs."""
    label_set = set(label_ids)
    if "IMPORTANT" in label_set and "STARRED" in label_set:
        return "high"
    if "IMPORTANT" in label_set:
        return "medium"
    return "low"


def _header_value(headers: list[dict], name: str) -> str:
    """Extract a header value by name (case-insensitive)."""
    name_lower = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lower:
            return h.get("value", "").strip()
    return ""


def _parse_received_at(date_str: str) -> str:
    """Convert an RFC 2822 Date header to ISO 8601 UTC string."""
    if not date_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:  # noqa: BLE001
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_filename(subject: str, message_id: str) -> str:
    """Build a filesystem-safe slug from email subject."""
    slug = subject.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    slug = slug[:60] or "no-subject"
    # Append short message-id suffix to guarantee uniqueness
    short_id = message_id[-8:]
    return f"email-{slug}-{short_id}.md"


def _extract_email_data(msg: dict) -> dict:
    """Return a structured dict with the fields we care about."""
    headers = msg.get("payload", {}).get("headers", [])
    label_ids = msg.get("labelIds", [])

    return {
        "message_id": msg["id"],
        "thread_id": msg.get("threadId", ""),
        "from": _header_value(headers, "From"),
        "subject": _header_value(headers, "Subject") or "(no subject)",
        "snippet": msg.get("snippet", "").strip(),
        "received_at": _parse_received_at(_header_value(headers, "Date")),
        "priority": _parse_priority(label_ids),
    }


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _render_markdown(email: dict) -> str:
    """Render a markdown document with YAML frontmatter for a single email."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Escape YAML-unsafe characters in string values
    def _esc(val: str) -> str:
        return val.replace('"', '\\"')

    frontmatter = (
        "---\n"
        "type: email\n"
        "status: pending\n"
        "requires_approval: false\n"
        f'from: "{_esc(email["from"])}"\n'
        f'subject: "{_esc(email["subject"])}"\n'
        f'received_at: "{email["received_at"]}"\n'
        f'priority: {email["priority"]}\n'
        f'gmail_message_id: "{email["message_id"]}"\n'
        f'gmail_thread_id: "{email["thread_id"]}"\n'
        f'created_at: "{now}"\n'
        "---\n"
    )

    body = (
        f"# Email: {email['subject']}\n\n"
        f"**From:** {email['from']}  \n"
        f"**Received:** {email['received_at']}  \n"
        f"**Priority:** {email['priority']}  \n\n"
        "## Snippet\n\n"
        f"{email['snippet']}\n\n"
        "## Actions Required\n\n"
        "- [ ] Review email content\n"
        "- [ ] Determine required response\n"
        "- [ ] Execute per Company Handbook\n"
        "- [ ] Mark complete when done\n"
    )

    return frontmatter + "\n" + body


# ---------------------------------------------------------------------------
# Writing to Needs_Action/
# ---------------------------------------------------------------------------

def _write_needs_action(email: dict) -> Path:
    """Write the markdown file into Needs_Action/ and return the path."""
    filename = _safe_filename(email["subject"], email["message_id"])
    dest = NEEDS_ACTION_DIR / filename

    # Handle unlikely collision (same subject, same short id within one poll)
    if dest.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        dest = NEEDS_ACTION_DIR / f"{dest.stem}-{ts}.md"

    content = _render_markdown(email)

    if DRY_RUN:
        logger.info("[DRY RUN] Would write: %s", dest)
        return dest

    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest


# ---------------------------------------------------------------------------
# Core poll cycle
# ---------------------------------------------------------------------------

def run_poll(service: Any, ledger: set[str]) -> dict:
    """Fetch unread important emails and create Needs_Action files.

    Returns a summary dict: {processed, skipped, errors}.
    """
    summary = {"processed": 0, "skipped": 0, "errors": []}

    logger.info("Fetching unread important emails (max %d)…", MAX_RESULTS)

    try:
        raw_messages = _with_retry(
            _fetch_unread_important, service, label="fetch_emails"
        )
    except Exception as exc:  # noqa: BLE001
        msg = f"Could not fetch emails: {exc}"
        logger.error(msg)
        summary["errors"].append(msg)
        return summary

    if not raw_messages:
        logger.info("No new unread important emails.")
        return summary

    logger.info("Found %d message(s) to evaluate.", len(raw_messages))

    for msg in raw_messages:
        msg_id = msg.get("id", "unknown")
        try:
            if msg_id in ledger:
                logger.debug("Skipping already-processed message: %s", msg_id)
                summary["skipped"] += 1
                continue

            email = _extract_email_data(msg)
            dest = _write_needs_action(email)

            # Mark as processed in ledger before logging so a crash mid-write
            # does not cause infinite re-processing on next poll.
            ledger.add(msg_id)
            _save_ledger(ledger)

            log_action(
                "email_received",
                dest.name,
                f"success | from={email['from']!r} | priority={email['priority']}",
            )
            logger.info(
                "Created: %s  [priority=%s, from=%s]",
                dest.name,
                email["priority"],
                email["from"],
            )
            summary["processed"] += 1

        except Exception as exc:  # noqa: BLE001
            err_msg = f"Error processing message {msg_id}: {exc}"
            logger.error(err_msg, exc_info=True)
            log_action("email_error", msg_id, f"error: {exc}")
            summary["errors"].append(err_msg)

    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Silver Tier Gmail Watcher — polls Gmail and writes to Needs_Action/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help=(
            f"Run continuously, polling every POLL_INTERVAL_SECONDS "
            f"(default: {POLL_INTERVAL}s). Without this flag, runs one poll then exits."
        ),
    )
    args = parser.parse_args()

    if DRY_RUN:
        logger.info("=== DRY RUN MODE — no files will be written ===")

    set_default_logs_dir(LOGS_DIR)
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)

    ledger = _load_ledger()
    logger.info("Ledger loaded: %d previously processed message(s).", len(ledger))

    service = _build_gmail_service()

    if args.watch:
        logger.info(
            "Watch mode — polling every %ds. Press Ctrl-C to stop.", POLL_INTERVAL
        )
        try:
            while True:
                summary = run_poll(service, ledger)
                logger.info(
                    "Poll complete — processed=%d, skipped=%d, errors=%d",
                    summary["processed"],
                    summary["skipped"],
                    len(summary["errors"]),
                )
                if summary["errors"]:
                    for err in summary["errors"]:
                        logger.warning("  Error: %s", err)
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Gmail watcher stopped.")
    else:
        summary = run_poll(service, ledger)
        logger.info(
            "Done — processed=%d, skipped=%d, errors=%d",
            summary["processed"],
            summary["skipped"],
            len(summary["errors"]),
        )
        if summary["errors"]:
            for err in summary["errors"]:
                logger.warning("  Error: %s", err)
        sys.exit(1 if summary["errors"] else 0)


if __name__ == "__main__":
    main()
