#!/usr/bin/env python3
"""Silver Tier WhatsApp Watcher.

Uses Playwright (async) with a persistent browser context to monitor WhatsApp
Web for unread chats. When a message matches a keyword trigger, a structured
markdown file is written to AI-Employee-Vault/Needs_Action/.

Usage:
    python3.14 whatsapp_watcher.py              # run one poll cycle then exit
    python3.14 whatsapp_watcher.py --watch      # poll on a schedule
    DRY_RUN=true python3.14 whatsapp_watcher.py # log without writing files

Environment variables:
    VAULT_PATH                Path to AI-Employee vault (default: ./AI-Employee-Vault)
    WA_PROFILE_DIR            Playwright persistent context dir (default: .whatsapp_profile)
    POLL_INTERVAL_SECONDS     Seconds between polls in --watch mode (default: 60)
    DRY_RUN                   Set to "true" to skip all writes (default: false)
    LOG_LEVEL                 DEBUG/INFO/WARNING/ERROR (default: INFO)
    WA_HEADLESS               Run browser headless (default: false)

Keyword triggers (case-insensitive):
    invoice, payment, urgent, project, proposal

Risk level auto-detection:
    high   — "urgent" or "payment" present
    medium — "invoice" or "proposal" present
    low    — all other keyword matches (e.g. "project")
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Gemini API (optional — gracefully skipped if not installed)
try:
    from google import genai as _genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.utils.logger import log_action, set_default_logs_dir  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_PATH = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
PENDING_APPROVAL_DIR = VAULT_PATH / "Pending_Approval"
APPROVED_DIR = VAULT_PATH / "Approved"
REJECTED_DIR = VAULT_PATH / "Rejected"
LOGS_DIR = VAULT_PATH / "Logs"

WA_PROFILE_DIR = Path(
    os.getenv("WA_PROFILE_DIR", ROOT / ".whatsapp_profile")
).resolve()

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")
WA_HEADLESS: bool = os.getenv("WA_HEADLESS", "false").lower() in ("true", "1", "yes")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")

MAX_RETRIES = 4
RETRY_BASE_DELAY = 2.0

KEYWORDS: list[str] = ["invoice", "payment", "urgent", "project", "proposal"]

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
AUTO_REPLY: bool = os.getenv("WA_AUTO_REPLY", "false").lower() in ("true", "1", "yes")

PAGE_TIMEOUT = 30_000
CHAT_LOAD_TIMEOUT = 10_000
WA_URL = "https://web.whatsapp.com"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def _build_logger() -> logging.Logger:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger("whatsapp_watcher")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | whatsapp_watcher | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fh = logging.FileHandler(
        LOGS_DIR / f"whatsapp-watcher-{today}.log", encoding="utf-8"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


logger = _build_logger()

# ---------------------------------------------------------------------------
# Async retry helper with exponential backoff
# ---------------------------------------------------------------------------


async def _with_retry_async(fn, *args, label: str = "operation", **kwargs):
    """Call async fn(*args, **kwargs) with exponential backoff."""
    delay = RETRY_BASE_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            if attempt == MAX_RETRIES:
                logger.error("%s failed after %d attempts: %s", label, MAX_RETRIES, exc)
                raise
            logger.warning(
                "%s attempt %d/%d failed (%s). Retrying in %.1fs…",
                label, attempt, MAX_RETRIES, exc, delay,
            )
            await asyncio.sleep(delay)
            delay *= 2


# ---------------------------------------------------------------------------
# Playwright session management (async)
# ---------------------------------------------------------------------------


async def _launch_context(playwright):
    """Launch a Playwright persistent browser context."""
    WA_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=str(WA_PROFILE_DIR),
        headless=WA_HEADLESS,
        args=["--no-sandbox", "--disable-setuid-sandbox"],
        viewport={"width": 1280, "height": 900},
        locale="en-US",
    )

    pages = context.pages
    page = pages[0] if pages else await context.new_page()
    page.set_default_timeout(PAGE_TIMEOUT)

    return context, page


async def _validate_session(page) -> bool:
    """Return True if WhatsApp Web chat list is visible (logged in)."""
    try:
        current = page.url
        if not current.startswith(WA_URL):
            logger.info("Navigating to WhatsApp Web…")
            await page.goto(WA_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)

        # Wait up to 45s for chat list — WA Web can take 30-40s on first load
        await page.wait_for_selector(
            'div[aria-label="Chat list"]',
            timeout=45_000,
        )
        logger.debug("Session validated — WhatsApp Web is active.")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Session validation failed: %s", exc)
        return False


async def _wait_for_qr_or_login(page) -> bool:
    """Wait for QR scan or existing login. Returns True when logged in."""
    # Keep navigating back if WhatsApp redirects to post_logout or elsewhere
    for attempt in range(5):
        current_url = page.url
        if "post_logout" in current_url or (
            current_url != WA_URL and not current_url.startswith(WA_URL + "/")
        ):
            logger.info(
                "Redirect detected (%s) — navigating back to WhatsApp Web (attempt %d)…",
                current_url, attempt + 1,
            )
            try:
                await page.goto(WA_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
            except Exception:  # noqa: BLE001
                await asyncio.sleep(2)
            continue

        try:
            # Wait up to 30s for either the chat list OR the QR canvas to appear
            await page.wait_for_selector(
                'div[aria-label="Chat list"], canvas[aria-label="Scan me!"], '
                'div[data-testid="qrcode"], div[data-ref]',
                timeout=30_000,
            )
        except Exception:  # noqa: BLE001
            # Still loading — check URL and retry
            await asyncio.sleep(3)
            continue

        # Check if already logged in
        chat_list = await page.query_selector('div[aria-label="Chat list"]')
        if chat_list:
            logger.info("Already logged in.")
            return True

        # QR code is visible — wait for user to scan (3 minutes)
        logger.info("QR code visible — please scan with your phone. You have 3 minutes.")
        try:
            await page.wait_for_selector(
                'div[aria-label="Chat list"]',
                timeout=180_000,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("QR scan timed out (3 min): %s", exc)
            return False

    logger.error("Could not reach WhatsApp Web login page after multiple attempts.")
    return False


# ---------------------------------------------------------------------------
# Chat scraping (async)
# ---------------------------------------------------------------------------


async def _get_unread_chats(page) -> list[dict]:
    """Return list of unread chat dicts."""
    # WhatsApp Web uses a virtualized list with role="row" inside role="grid"
    try:
        await page.wait_for_selector(
            'div[aria-label="Chat list"] div[role="row"]',
            timeout=CHAT_LOAD_TIMEOUT,
        )
    except Exception:  # noqa: BLE001
        logger.debug("No chat rows found within timeout.")
        return []

    chats: list[dict] = []
    chat_items = await page.query_selector_all(
        'div[aria-label="Chat list"] div[role="row"]'
    )

    for item in chat_items:
        badge = await item.query_selector('span[aria-label*="unread"]')
        if badge is None:
            badge = await item.query_selector(
                'span._ahlk, span[data-testid="icon-unread-count"]'
            )
        if badge is None:
            continue

        name_el = await item.query_selector('span[dir="auto"][title]')
        if name_el:
            sender = (await name_el.get_attribute("title") or "").strip()
        else:
            name_el = await item.query_selector('span[dir="auto"]')
            sender = (await name_el.inner_text()).strip() if name_el else "Unknown"

        badge_count = (await badge.inner_text()).strip()
        chats.append({"sender": sender, "badge_count": badge_count, "element": item})

    logger.debug("Found %d unread chat(s).", len(chats))
    return chats


async def _open_chat(page, chat_item) -> bool:
    """Click a chat and wait for message pane."""
    try:
        await chat_item["element"].click()
        # Wait for message rows or copyable text (works with current WhatsApp Web)
        await page.wait_for_selector(
            'div[class*="message"], span.copyable-text, div[data-id]',
            timeout=CHAT_LOAD_TIMEOUT,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not open chat for %r: %s", chat_item["sender"], exc)
        return False


async def _extract_latest_message(page) -> Optional[dict]:
    """Return last message text and timestamp from open conversation."""
    try:
        # Try span.copyable-text first (most reliable in current WA Web)
        text_els = await page.query_selector_all("span.copyable-text")
        if text_els:
            text = (await text_els[-1].inner_text()).strip()
            # Timestamp is in the data-pre-plain-text attribute of the copyable-text span
            raw_attr = await text_els[-1].get_attribute("data-pre-plain-text") or ""
            # Format: "[HH:MM, DD/MM/YYYY] Sender: "
            import re as _re
            ts_match = _re.search(r"\[([^\]]+)\]", raw_attr)
            timestamp = ts_match.group(1) if ts_match else ""
            if text:
                return {"text": text, "timestamp": timestamp}

        # Fallback: div[class*="message"] containers
        bubbles = await page.query_selector_all('div[class*="message"]')
        if not bubbles:
            return None
        last = bubbles[-1]
        text = (await last.inner_text()).strip()
        if text:
            return {"text": text, "timestamp": ""}
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to extract message: %s", exc)
        return None


# ---------------------------------------------------------------------------
# AI Reply Generator
# ---------------------------------------------------------------------------


def _generate_ai_reply(sender: str, message: str) -> Optional[str]:
    """Gemini se AI reply generate karo incoming message ke liye."""
    if not _GENAI_AVAILABLE or not GEMINI_API_KEY:
        logger.debug("Gemini unavailable — AI reply skip.")
        return None
    try:
        client = _genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            f"You are a helpful professional assistant replying to a WhatsApp message on behalf of the user.\n\n"
            f"Sender: {sender}\n"
            f"Their message: {message}\n\n"
            f"Write a short, natural, professional reply (1-3 sentences). "
            f"Match the language/tone of the incoming message. "
            f"Do NOT add any explanation — output ONLY the reply text."
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        reply = response.text.strip()
        logger.info("AI reply generated for %r: %s", sender, reply[:80])
        return reply
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI reply generation failed: %s", exc)
        return None


def _generate_ai_outbound(contact: str, instruction: str) -> str:
    """Vault command se outbound message generate karo (e.g. 'greetings bhejo')."""
    if _GENAI_AVAILABLE and GEMINI_API_KEY:
        try:
            client = _genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                f"You are writing a WhatsApp message on behalf of the user.\n\n"
                f"Contact: {contact}\n"
                f"Instruction: {instruction}\n\n"
                f"Write a short, friendly WhatsApp message. "
                f"Match the language/tone of the instruction (Urdu/Roman Urdu/English). "
                f"Add emoji if it fits. Output ONLY the message text."
            )
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            return response.text.strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Outbound AI message failed: %s", exc)
    return f"Hello {contact}! Hope you are doing well. 😊"


# ---------------------------------------------------------------------------
# Send message to currently open chat
# ---------------------------------------------------------------------------


async def _send_message_in_open_chat(page, message: str) -> bool:
    """Currently open WhatsApp chat mein message type karo aur send karo."""
    try:
        # Message input box — WhatsApp Web ka main text input
        msg_box = await page.wait_for_selector(
            'div[contenteditable="true"][data-tab="10"], '
            'div[role="textbox"][data-tab="10"], '
            'footer div[contenteditable="true"]',
            timeout=8_000,
        )
        await msg_box.click()
        await asyncio.sleep(0.3)

        # Multi-line support
        lines = message.split("\n")
        for i, line in enumerate(lines):
            await msg_box.type(line, delay=25)
            if i < len(lines) - 1:
                await page.keyboard.press("Shift+Enter")

        await asyncio.sleep(0.4)

        if DRY_RUN:
            logger.info("[DRY RUN] Message typed but NOT sent: %s", message[:80])
            await page.keyboard.press("Control+a")
            await page.keyboard.press("Backspace")
            return True

        # --- SEND: try multiple strategies until message is sent ---

        for attempt in range(1, 4):
            logger.info("Send attempt %d/3...", attempt)

            # Check if text is still in the input box
            still_has_text = await page.evaluate(
                '() => { const el = document.querySelector(\'div[contenteditable="true"][data-tab="10"], footer div[contenteditable="true"]\'); return el ? el.textContent.trim().length > 0 : false; }'
            )
            if not still_has_text:
                logger.info("Message sent successfully (input box is empty).")
                break

            if attempt == 1:
                # Strategy 1: Playwright locator force-click on send button
                try:
                    loc = page.locator('button[aria-label="Send"], button[data-testid="compose-btn-send"]').first
                    await loc.click(force=True, timeout=3000)
                    logger.info("Playwright locator force-click executed.")
                    await asyncio.sleep(2)
                    continue
                except Exception:
                    logger.info("Locator click failed, trying next strategy...")

            if attempt == 2:
                # Strategy 2: dispatchEvent with mouse+pointer events (for React)
                await page.evaluate('''() => {
                    const icon = document.querySelector('span[data-icon="send"]');
                    const btn = icon ? (icon.closest('button') || icon.parentElement) : document.querySelector('button[aria-label="Send"]');
                    if (btn) {
                        const opts = {bubbles: true, cancelable: true, view: window};
                        btn.dispatchEvent(new MouseEvent('mousedown', opts));
                        btn.dispatchEvent(new MouseEvent('mouseup', opts));
                        btn.dispatchEvent(new MouseEvent('click', opts));
                        btn.dispatchEvent(new PointerEvent('pointerdown', opts));
                        btn.dispatchEvent(new PointerEvent('pointerup', opts));
                    }
                }''')
                logger.info("dispatchEvent (mouse+pointer events) fired.")
                await asyncio.sleep(2)
                continue

            if attempt == 3:
                # Strategy 3: Enter key on message box (simplest fallback)
                await msg_box.click()
                await asyncio.sleep(0.3)
                await page.keyboard.press("Enter")
                logger.info("Enter key pressed on message box.")
                await asyncio.sleep(2)

        logger.info("Send sequence complete.")
        return True

    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to send message: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Find contact and open chat (for outbound commands)
# ---------------------------------------------------------------------------


async def _find_and_open_contact(page, contact_name: str) -> bool:
    """Search box se contact dhundho aur chat kholo."""
    try:
        logger.info("Searching contact: %r", contact_name)

        # Search box click karo
        search_btn = await page.query_selector(
            'button[aria-label="Search or start new chat"], '
            'div[data-testid="chat-list-search"]'
        )
        if search_btn:
            await search_btn.click()
        else:
            await page.click('div[contenteditable="true"][data-tab="3"]')
        await asyncio.sleep(0.5)

        search_box = await page.wait_for_selector(
            'div[contenteditable="true"][data-tab="3"], '
            'div[role="textbox"][title="Search input textbox"]',
            timeout=5_000,
        )
        await search_box.fill("")
        await search_box.type(contact_name, delay=50)
        await asyncio.sleep(1.5)

        # Find the correct contact from search results (match by name)
        results = await page.query_selector_all(
            'div[aria-label="Search results."] div[role="row"], '
            'div[aria-label="Chat list"] div[role="row"]'
        )
        if not results:
            logger.error("Contact %r not found in search.", contact_name)
            return False

        # Check each result's title/name — click the closest match
        target = contact_name.lower().strip()
        best_match = None
        for row in results:
            title_el = await row.query_selector('span[title]')
            if title_el:
                title_text = await title_el.get_attribute("title")
                if title_text and target in title_text.lower():
                    best_match = row
                    logger.info("Exact match found: %r", title_text)
                    break

        if not best_match:
            logger.warning("No exact match for %r — using first result as fallback.", contact_name)
            best_match = results[0]

        await best_match.click()
        await asyncio.sleep(1.0)

        # Chat input box ka wait karo
        await page.wait_for_selector(
            'div[contenteditable="true"][data-tab="10"], '
            'footer div[contenteditable="true"]',
            timeout=8_000,
        )
        logger.info("Chat opened for: %r", contact_name)
        return True

    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not open contact %r: %s", contact_name, exc)
        return False


# ---------------------------------------------------------------------------
# Vault command processor (outbound messages)
# ---------------------------------------------------------------------------


async def process_outbound_commands(page) -> None:
    """
    Needs_Action folder mein whatsapp-send-*.md files check karo.
    Format:
        ---
        type: whatsapp_send
        contact: "Areeba Jazz"
        instruction: "greetings bhejo"
        ---
    """
    send_files = list(NEEDS_ACTION_DIR.glob("whatsapp-send-*.md"))
    if not send_files:
        return

    logger.info("Found %d outbound WhatsApp command(s).", len(send_files))

    for cmd_file in send_files:
        try:
            content = cmd_file.read_text(encoding="utf-8")

            # YAML frontmatter parse
            contact = ""
            instruction = ""
            for line in content.splitlines():
                if line.startswith("contact:"):
                    contact = line.split(":", 1)[1].strip().strip('"')
                elif line.startswith("instruction:"):
                    instruction = line.split(":", 1)[1].strip().strip('"')

            if not contact:
                logger.warning("No contact in %s — skipping.", cmd_file.name)
                cmd_file.unlink()
                continue

            # AI message generate karo
            message = _generate_ai_outbound(contact, instruction or "greetings bhejo")
            logger.info("Outbound to %r: %s", contact, message[:80])

            # Contact dhundho aur send karo
            if await _find_and_open_contact(page, contact):
                await _send_message_in_open_chat(page, message)
                log_action("whatsapp_sent", contact, f"success | msg={message[:60]}")
            else:
                log_action("whatsapp_send_failed", contact, "contact not found")

            # Command file delete karo (processed)
            cmd_file.unlink()
            logger.info("Command file processed and removed: %s", cmd_file.name)

        except Exception as exc:  # noqa: BLE001
            logger.error("Error processing outbound command %s: %s", cmd_file.name, exc)


# ---------------------------------------------------------------------------
# Keyword filtering and risk scoring
# ---------------------------------------------------------------------------


def _matches_keywords(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in KEYWORDS)


def _detect_risk(text: str) -> str:
    lower = text.lower()
    if "urgent" in lower or "payment" in lower:
        return "high"
    if "invoice" in lower or "proposal" in lower:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Markdown generation and file writing
# ---------------------------------------------------------------------------


def _safe_filename(sender: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", sender.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-") or "unknown"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"whatsapp-{slug[:40]}-{ts}.md"


def _esc_yaml(val: str) -> str:
    return val.replace('"', '\\"').replace("\n", " ")


def _render_markdown(sender: str, message: str, timestamp: str, risk: str) -> str:
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter = (
        "---\n"
        "type: whatsapp\n"
        f'sender: "{_esc_yaml(sender)}"\n'
        f'message: "{_esc_yaml(message)}"\n'
        f'received: "{_esc_yaml(timestamp)}"\n'
        f"risk_level: {risk}\n"
        "requires_approval: false\n"
        f'created_at: "{now_iso}"\n'
        "---\n"
    )
    body = (
        f"# WhatsApp: {sender}\n\n"
        f"**Sender:** {sender}  \n"
        f"**Received:** {timestamp}  \n"
        f"**Risk Level:** {risk}  \n\n"
        "## Message\n\n"
        f"{message}\n\n"
        "## Actions Required\n\n"
        "- [ ] Review message content\n"
        "- [ ] Determine required response\n"
        "- [ ] Execute per Company Handbook\n"
        "- [ ] Mark complete when done\n"
    )
    return frontmatter + "\n" + body


def _write_needs_action(sender: str, message: str, timestamp: str, risk: str) -> Path:
    filename = _safe_filename(sender)
    dest = NEEDS_ACTION_DIR / filename
    content = _render_markdown(sender, message, timestamp, risk)

    if DRY_RUN:
        logger.info("[DRY RUN] Would write: %s", dest)
        return dest

    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest


# ---------------------------------------------------------------------------
# Backend activity notification
# ---------------------------------------------------------------------------


def _notify_backend_activity(event_type: str, description: str, metadata: dict | None = None) -> None:
    """Fire-and-forget POST to backend activity-logs endpoint.

    Silently swallows errors so watcher never crashes due to backend unavailability.
    """
    if DRY_RUN:
        return
    try:
        payload = json.dumps({
            "type": event_type,
            "description": description,
            "metadata": metadata or {},
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{BACKEND_API_URL}/activity-logs",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception as exc:  # noqa: BLE001
        logger.debug("Backend activity notification failed (non-critical): %s", exc)


# ---------------------------------------------------------------------------
# Pending approval: reply save karo (seedha send nahi)
# ---------------------------------------------------------------------------


def _write_pending_reply(sender: str, original_message: str, proposed_reply: str) -> Path:
    """
    AI-generated reply ko Pending_Approval/ mein save karo.
    Aap file dekhen:
      - Approve: file ko Approved/ mein move karen
      - Reject:  file ko Rejected/ mein move karen (ya delete karen)
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    slug = re.sub(r"[^\w\s-]", "", sender.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-") or "unknown"
    filename = f"whatsapp-reply-{slug[:40]}-{ts}.md"

    content = (
        "---\n"
        "type: whatsapp_reply_pending\n"
        f'contact: "{_esc_yaml(sender)}"\n'
        f'proposed_reply: "{_esc_yaml(proposed_reply)}"\n'
        f'original_message: "{_esc_yaml(original_message)}"\n'
        f'created_at: "{now_iso}"\n'
        "---\n\n"
        f"# WhatsApp Reply Pending Approval: {sender}\n\n"
        f"**Contact:** {sender}\n\n"
        "## Original Message Received\n\n"
        f"{original_message}\n\n"
        "## Proposed AI Reply\n\n"
        f"{proposed_reply}\n\n"
        "## Instructions\n\n"
        "- **Approve:** Move this file to `Approved/` folder\n"
        "- **Reject:** Move this file to `Rejected/` folder (or delete it)\n"
        "- Watcher next poll mein `Approved/` check karega aur tabhí send karega\n"
    )

    if DRY_RUN:
        logger.info("[DRY RUN] Would write pending reply: %s", filename)
        return PENDING_APPROVAL_DIR / filename

    PENDING_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    dest = PENDING_APPROVAL_DIR / filename
    dest.write_text(content, encoding="utf-8")
    logger.info("Pending reply saved (awaiting your approval): %s", filename)
    return dest


# ---------------------------------------------------------------------------
# Approved reply sender
# ---------------------------------------------------------------------------


async def process_approved_replies(page) -> None:
    """
    Approved/ folder mein whatsapp-reply-*.md files check karo.
    Agar file hai toh contact dhundho aur reply bhejo.
    """
    approved_files = list(APPROVED_DIR.glob("whatsapp-reply-*.md"))
    if not approved_files:
        return

    logger.info("Found %d approved WhatsApp reply/replies to send.", len(approved_files))

    for reply_file in approved_files:
        contact = ""
        proposed_reply = ""
        try:
            content = reply_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("contact:"):
                    contact = line.split(":", 1)[1].strip().strip('"')
                elif line.startswith("proposed_reply:"):
                    proposed_reply = line.split(":", 1)[1].strip().strip('"')

            if not contact or not proposed_reply:
                logger.warning("Incomplete approved reply file %s — skipping.", reply_file.name)
                reply_file.unlink(missing_ok=True)
                continue

            logger.info("Sending approved reply to %r: %s", contact, proposed_reply[:80])

            if await _find_and_open_contact(page, contact):
                sent = await _send_message_in_open_chat(page, proposed_reply)
                if sent:
                    logger.info("Approved reply sent to %r.", contact)
                    log_action("whatsapp_auto_reply_sent", contact, f"approved | msg={proposed_reply[:60]}")
                    _notify_backend_activity(
                        "whatsapp.reply_sent",
                        f"Approved reply sent to {contact}: {proposed_reply[:100]}",
                        {"contact": contact},
                    )
                else:
                    logger.warning("Failed to send approved reply to %r.", contact)
            else:
                logger.error("Contact %r not found — could not send reply.", contact)

        except Exception as exc:  # noqa: BLE001
            logger.error("Error sending approved reply from %s: %s", reply_file.name, exc)
        finally:
            # Processed file delete karo (sent ya failed)
            reply_file.unlink(missing_ok=True)
            logger.debug("Approved reply file removed: %s", reply_file.name)


# ---------------------------------------------------------------------------
# Core poll cycle (async)
# ---------------------------------------------------------------------------


async def run_poll(page) -> dict:
    """Scrape unread chats and create Needs_Action files."""
    summary: dict = {"processed": 0, "skipped": 0, "errors": []}

    logger.info("Fetching unread chats…")

    try:
        unread = await _with_retry_async(
            _get_unread_chats, page, label="get_unread_chats"
        )
    except Exception as exc:  # noqa: BLE001
        msg = f"Could not fetch unread chats: {exc}"
        logger.error(msg)
        summary["errors"].append(msg)
        return summary

    if not unread:
        logger.info("No unread chats found.")
        return summary

    logger.info("Found %d unread chat(s) to evaluate.", len(unread))

    for chat in unread:
        sender = chat["sender"]
        try:
            if not await _open_chat(page, chat):
                summary["skipped"] += 1
                continue

            msg_data = await _with_retry_async(
                _extract_latest_message, page, label=f"extract_message:{sender}"
            )

            if msg_data is None:
                logger.debug("No extractable message in chat with %r — skipping.", sender)
                summary["skipped"] += 1
                continue

            message_text = msg_data["text"]
            timestamp = msg_data["timestamp"] or datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

            if not _matches_keywords(message_text):
                logger.debug("Chat with %r has no keyword match — skipping.", sender)
                summary["skipped"] += 1
                continue

            risk = _detect_risk(message_text)
            dest = _write_needs_action(sender, message_text, timestamp, risk)

            log_action(
                "whatsapp_received",
                dest.name,
                f"success | sender={sender!r} | risk={risk}",
            )
            _notify_backend_activity(
                "whatsapp.received",
                f"WhatsApp message from {sender}: {message_text[:120]}",
                {"sender": sender, "risk_level": risk, "vault_file": dest.name},
            )
            logger.info("Created: %s  [risk=%s, sender=%s]", dest.name, risk, sender)

            # Auto-reply: AI reply generate karo aur Pending_Approval mein save karo
            # (seedha send NAHI karta — pehle aapki permission chahiye)
            if AUTO_REPLY:
                reply = _generate_ai_reply(sender, message_text)
                if reply:
                    _write_pending_reply(sender, message_text, reply)

            summary["processed"] += 1

        except Exception as exc:  # noqa: BLE001
            err_msg = f"Error processing chat with {sender!r}: {exc}"
            logger.error(err_msg, exc_info=True)
            log_action("whatsapp_error", sender, f"error: {exc}")
            summary["errors"].append(err_msg)

    return summary


# ---------------------------------------------------------------------------
# Main async entry point
# ---------------------------------------------------------------------------


async def _async_main(watch: bool) -> None:
    try:
        from playwright.async_api import async_playwright  # noqa: PLC0415
    except ImportError as exc:
        logger.error(
            "Playwright not installed. Run:\n"
            "  pip install playwright && python3.14 -m playwright install chromium\n"
            "Error: %s", exc,
        )
        raise SystemExit(1) from exc

    if DRY_RUN:
        logger.info("=== DRY RUN MODE — no files will be written ===")

    set_default_logs_dir(LOGS_DIR)
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    PENDING_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Launching browser context (profile: %s)…", WA_PROFILE_DIR)

    async with async_playwright() as pw:
        # Exponential retry for browser launch
        delay = RETRY_BASE_DELAY
        context = None
        page = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                context, page = await _launch_context(pw)
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == MAX_RETRIES:
                    logger.error("Browser launch failed after %d attempts: %s", MAX_RETRIES, exc)
                    raise SystemExit(1) from exc
                logger.warning(
                    "Browser launch attempt %d/%d failed (%s). Retrying in %.1fs…",
                    attempt, MAX_RETRIES, exc, delay,
                )
                await asyncio.sleep(delay)
                delay *= 2

        try:
            # Validate or establish session
            if not await _validate_session(page):
                logger.info("Not logged in — starting QR login flow.")
                await page.goto(WA_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
                if not await _wait_for_qr_or_login(page):
                    logger.error("Could not establish WhatsApp Web session. Exiting.")
                    raise SystemExit(1)

            logger.info("WhatsApp Web session is active.")

            if watch:
                logger.info(
                    "Watch mode — polling every %ds. Press Ctrl-C to stop.", POLL_INTERVAL
                )
                while True:
                    try:
                        if not await _validate_session(page):
                            logger.warning("Session lost — attempting goto…")
                            await page.goto(WA_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
                            if not await _validate_session(page):
                                logger.error("Could not re-establish session. Stopping.")
                                break

                        summary = await run_poll(page)
                        logger.info(
                            "Poll complete — processed=%d skipped=%d errors=%d",
                            summary["processed"], summary["skipped"], len(summary["errors"]),
                        )
                        # Approved replies bhejo (aapki permission ke baad)
                        await process_approved_replies(page)
                        # Outbound commands check karo (vault se send instructions)
                        await process_outbound_commands(page)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Watch loop error (will retry next cycle): %s", exc)
                    await asyncio.sleep(POLL_INTERVAL)
            else:
                summary = await run_poll(page)
                logger.info(
                    "Poll complete — processed=%d skipped=%d errors=%d",
                    summary["processed"], summary["skipped"], len(summary["errors"]),
                )
                await process_approved_replies(page)
                await process_outbound_commands(page)

        finally:
            logger.info("Closing browser context.")
            try:
                await context.close()
            except Exception:  # noqa: BLE001
                pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Silver Tier WhatsApp Watcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help=f"Poll continuously every {POLL_INTERVAL}s. Without flag: single poll then exit.",
    )
    args = parser.parse_args()
    asyncio.run(_async_main(watch=args.watch))


if __name__ == "__main__":
    main()
