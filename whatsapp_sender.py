#!/usr/bin/env python3
"""WhatsApp AI Sender.

AI-generated message banao aur WhatsApp Web se kisi bhi contact ko send karo.

Usage:
    python3 whatsapp_sender.py "areeba ko greetings bhejo"
    python3 whatsapp_sender.py "jazz waly ko invoice reminder bhejo"
    python3 whatsapp_sender.py --contact "Areeba" --instruction "greetings bhejo"

Environment variables:
    GEMINI_API_KEY        Gemini API key (required)
    WA_PROFILE_DIR        Playwright persistent context dir (default: .whatsapp_profile)
    WA_HEADLESS           Run browser headless (default: false)
    DRY_RUN               Set to "true" to only generate message, don't send (default: false)
"""

import argparse
import asyncio
import logging
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WA_PROFILE_DIR = Path(
    os.getenv("WA_PROFILE_DIR", ROOT / ".whatsapp_profile")
).resolve()

WA_HEADLESS: bool = os.getenv("WA_HEADLESS", "false").lower() in ("true", "1", "yes")
DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

PAGE_TIMEOUT = 30_000
WA_URL = "https://web.whatsapp.com"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | whatsapp_sender | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("whatsapp_sender")

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# AI Message Generator (Gemini)
# ---------------------------------------------------------------------------


def generate_message(contact_name: str, instruction: str) -> str:
    """Gemini se AI-generated WhatsApp message banao."""

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY nahi mili — default message use ho raha hai.")
        return f"Hello {contact_name}! Hope you are doing well. 😊"

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""You are a helpful assistant writing a WhatsApp message on behalf of the user.

Contact name: {contact_name}
User instruction: {instruction}

Write a natural, friendly WhatsApp message in the same language as the instruction.
- If instruction is in Urdu/Roman Urdu, write message in Roman Urdu or English (whichever fits better for WhatsApp)
- Keep it concise (1-4 sentences max)
- Add appropriate emoji if it fits
- Do NOT add any explanation, just write the message text only

Message:"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        message = response.text.strip()
        logger.info("AI message generate hua: %s", message[:80])
        return message

    except Exception as exc:
        logger.error("Gemini se message generate karne mein error: %s", exc)
        return f"Hello {contact_name}! Hope you are doing well. 😊"


# ---------------------------------------------------------------------------
# Instruction Parser — contact aur instruction extract karo
# ---------------------------------------------------------------------------


def parse_instruction(raw: str) -> tuple[str, str]:
    """
    Natural language instruction se contact name aur action extract karo.

    Examples:
        "areeba ko greetings bhejo"  -> ("areeba", "greetings bhejo")
        "jazz waly ko invoice reminder bhejo" -> ("jazz waly", "invoice reminder bhejo")
        "Ali ko bolo kal meeting hai" -> ("Ali", "kal meeting hai")
    """
    # Pattern: "<contact> ko <message/instruction>"
    match = re.search(r"^(.+?)\s+ko\s+(.+)$", raw.strip(), re.IGNORECASE)
    if match:
        contact = match.group(1).strip()
        action = match.group(2).strip()
        return contact, action

    # Fallback: pehla word contact, baaki instruction
    parts = raw.strip().split(None, 1)
    if len(parts) == 2:
        return parts[0], parts[1]

    return raw.strip(), "Hello bhejo"


# ---------------------------------------------------------------------------
# Playwright — WhatsApp Web session
# ---------------------------------------------------------------------------


async def _launch_context(playwright):
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


async def _ensure_logged_in(page) -> bool:
    """WhatsApp Web mein logged in hai ya nahi check karo, zaroorat ho to QR scan karao."""
    try:
        current = page.url
        if not current.startswith(WA_URL):
            logger.info("WhatsApp Web pe ja raha hun...")
            await page.goto(WA_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)

        # Chat list ya QR code ka wait karo
        await page.wait_for_selector(
            'div[aria-label="Chat list"], canvas[aria-label="Scan me!"], div[data-testid="qrcode"]',
            timeout=45_000,
        )

        chat_list = await page.query_selector('div[aria-label="Chat list"]')
        if chat_list:
            logger.info("Already logged in.")
            return True

        # QR visible hai
        logger.info("QR code dikha raha hai — phone se scan karo. 3 minutes hain.")
        await page.wait_for_selector('div[aria-label="Chat list"]', timeout=180_000)
        logger.info("Login successful!")
        return True

    except Exception as exc:
        logger.error("Login nahi ho saka: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Contact Search aur Message Send
# ---------------------------------------------------------------------------


async def find_and_open_contact(page, contact_name: str) -> bool:
    """
    Contact search karo aur chat kholo.
    WhatsApp search box use karta hai - exact name ya partial match.
    """
    try:
        # Search icon / new chat button dhundho
        logger.info("Contact dhundh raha hun: %r", contact_name)

        # Search button click karo (magnifying glass)
        search_btn = await page.query_selector(
            'button[aria-label="Search or start new chat"], '
            'div[data-testid="chat-list-search"], '
            'span[data-testid="chat-list-search"]'
        )
        if search_btn:
            await search_btn.click()
            await asyncio.sleep(0.5)
        else:
            # Try clicking the search area directly
            await page.click('div[contenteditable="true"][data-tab="3"]')
            await asyncio.sleep(0.5)

        # Search box mein type karo
        search_box = await page.wait_for_selector(
            'div[contenteditable="true"][data-tab="3"], '
            'input[type="text"][title="Search or start new chat"], '
            'div[role="textbox"][title="Search input textbox"]',
            timeout=5_000,
        )
        await search_box.fill("")
        await search_box.type(contact_name, delay=50)
        await asyncio.sleep(1.5)  # results load hone do

        # Search results mein pehla result click karo
        first_result = await page.query_selector(
            'div[aria-label="Chat list"] div[role="row"]:first-child, '
            'div[data-testid="cell-frame-container"]:first-child'
        )
        if not first_result:
            # Try generic list item
            results = await page.query_selector_all(
                'div[aria-label="Search results."] div[role="row"], '
                'div[aria-label="Chat list"] div[role="row"]'
            )
            if results:
                first_result = results[0]

        if not first_result:
            logger.error("Contact %r nahi mila search mein.", contact_name)
            return False

        await first_result.click()
        await asyncio.sleep(1)

        # Chat khulne ka wait karo
        await page.wait_for_selector(
            'div[contenteditable="true"][data-tab="10"], '
            'div[role="textbox"][data-tab="10"], '
            'footer div[contenteditable="true"]',
            timeout=8_000,
        )
        logger.info("Chat khul gaya contact: %r", contact_name)
        return True

    except Exception as exc:
        logger.error("Contact dhundne mein error: %s", exc)
        return False


async def send_whatsapp_message(page, message: str) -> bool:
    """Open chat mein message type karo aur send karo."""
    try:
        # Message input box dhundho
        msg_box = await page.wait_for_selector(
            'div[contenteditable="true"][data-tab="10"], '
            'div[role="textbox"][data-tab="10"], '
            'footer div[contenteditable="true"]',
            timeout=8_000,
        )

        # Message type karo
        logger.info("Message type kar raha hun...")
        await msg_box.click()
        await asyncio.sleep(0.3)

        # Multi-line message ke liye lines alag type karo
        lines = message.split("\n")
        for i, line in enumerate(lines):
            await msg_box.type(line, delay=30)
            if i < len(lines) - 1:
                # Shift+Enter for new line in WhatsApp
                await page.keyboard.press("Shift+Enter")

        await asyncio.sleep(0.5)

        if DRY_RUN:
            logger.info("[DRY RUN] Message type hua lekin send nahi kiya: %s", message[:80])
            # Clear the typed message
            await page.keyboard.press("Control+a")
            await page.keyboard.press("Backspace")
            return True

        # Pehle send button try karo (zyada reliable hai)
        send_btn = await page.query_selector(
            'button[aria-label="Send"], '
            'span[data-icon="send"], '
            'button[data-testid="compose-btn-send"]'
        )
        if send_btn:
            logger.info("Send button mila — click kar raha hun...")
            await send_btn.click()
            await asyncio.sleep(1)
        else:
            # Fallback: Enter dabao message send karne ke liye
            logger.info("Send button nahi mila — Enter key try kar raha hun...")
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)

        # Verify: check karo ke message actually send hua ya nahi
        # Thoda wait karo aur dobara try karo agar pehli baar fail ho
        still_has_text = await page.evaluate(
            '() => { const el = document.querySelector(\'div[contenteditable="true"][data-tab="10"], footer div[contenteditable="true"]\'); return el ? el.textContent.trim().length > 0 : false; }'
        )
        if still_has_text:
            logger.warning("Pehli try mein send nahi hua — dobara try kar raha hun...")
            # Dobara send button try karo
            send_btn2 = await page.query_selector(
                'button[aria-label="Send"], '
                'span[data-icon="send"], '
                'button[data-testid="compose-btn-send"]'
            )
            if send_btn2:
                await send_btn2.click()
                await asyncio.sleep(1)
            else:
                await page.keyboard.press("Enter")
                await asyncio.sleep(1)

        logger.info("Message successfully send ho gaya!")
        return True

    except Exception as exc:
        logger.error("Message send karne mein error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Main async flow
# ---------------------------------------------------------------------------


async def _async_main(contact_name: str, instruction: str) -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        logger.error(
            "Playwright install nahi hai. Run karo:\n"
            "  pip install playwright && python3 -m playwright install chromium\n"
            "Error: %s", exc,
        )
        raise SystemExit(1) from exc

    # Step 1: AI message generate karo
    logger.info("AI se message generate ho raha hai...")
    message = generate_message(contact_name, instruction)
    print(f"\n{'='*50}")
    print(f"Contact  : {contact_name}")
    print(f"Message  : {message}")
    print(f"{'='*50}\n")

    if DRY_RUN:
        logger.info("[DRY RUN] Browser nahi khula — sirf message generate kiya.")
        return

    # Step 2: Browser kholo
    logger.info("Browser launch ho raha hai...")
    async with async_playwright() as pw:
        context, page = await _launch_context(pw)
        try:
            # Step 3: Login ensure karo
            if not await _ensure_logged_in(page):
                logger.error("WhatsApp login fail. Exiting.")
                raise SystemExit(1)

            # Step 4: Contact dhundho aur chat kholo
            if not await find_and_open_contact(page, contact_name):
                logger.error("Contact %r nahi mila. Exiting.", contact_name)
                raise SystemExit(1)

            # Step 5: Message send karo
            success = await send_whatsapp_message(page, message)
            if success:
                print(f"\n✅ Message successfully sent to {contact_name}!")
            else:
                print(f"\n❌ Message send karne mein problem aai.")
                raise SystemExit(1)

            # Thoda wait karo taake message deliver ho
            await asyncio.sleep(2)

        finally:
            await context.close()


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WhatsApp AI Sender — AI-generated message WhatsApp pe bhejo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 whatsapp_sender.py "areeba ko greetings bhejo"
  python3 whatsapp_sender.py "jazz waly ko invoice reminder bhejo"
  python3 whatsapp_sender.py --contact "Areeba" --instruction "kal ki meeting yaad dilao"
  DRY_RUN=true python3 whatsapp_sender.py "Ali ko good morning bhejo"
        """,
    )
    parser.add_argument(
        "instruction",
        nargs="?",
        help='Natural language instruction, e.g. "areeba ko greetings bhejo"',
    )
    parser.add_argument(
        "--contact",
        help="Contact name (agar alag dena ho)",
    )
    parser.add_argument(
        "--instruction",
        dest="instruction_flag",
        help="Instruction (agar alag dena ho)",
    )

    args = parser.parse_args()

    # Contact aur instruction resolve karo
    if args.contact and args.instruction_flag:
        contact_name = args.contact
        instruction = args.instruction_flag
    elif args.instruction:
        contact_name, instruction = parse_instruction(args.instruction)
    else:
        parser.print_help()
        raise SystemExit(0)

    logger.info("Contact: %r | Instruction: %r", contact_name, instruction)
    asyncio.run(_async_main(contact_name, instruction))


if __name__ == "__main__":
    main()
