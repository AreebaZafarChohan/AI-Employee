from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from app.config import settings
from app.routers import (
    vault, system, mcp, audit_logs, tasks, plans, activity_logs,
    goals, costs, tools, metrics, approvals, ai_agent,
    whatsapp, linkedin, sales, files, watchers, gmail,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Employee Backend API", version="v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGIN, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers under /api/v1
for r in [
    vault.router, system.router, mcp.router, audit_logs.router,
    tasks.router, plans.router, activity_logs.router,
    goals.router, costs.router, tools.router, metrics.router,
    approvals.router, ai_agent.router,
    whatsapp.router, linkedin.router, sales.router, files.router, watchers.router,
    gmail.router,
]:
    app.include_router(r, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "AI Employee Backend API",
        "version": "v1",
        "endpoints": {
            "tasks": "/api/v1/tasks",
            "plans": "/api/v1/plans",
            "activityLogs": "/api/v1/activity-logs",
            "system": {
                "state": "/api/v1/system/state",
                "health": "/api/v1/system/health",
                "mcpHealth": "/api/v1/system/mcp-health",
            },
            "auditLogs": "/api/v1/audit-logs",
            "approvals": "/api/v1/approvals/metrics",
            "whatsapp": {
                "messages": "/api/v1/whatsapp/messages",
                "send": "/api/v1/whatsapp/send",
                "status": "/api/v1/whatsapp/status",
                "receive": "/api/v1/whatsapp/receive",
            },
        },
    }


# ---------------------------------------------------------------------------
# WebSocket — shared client list
# ---------------------------------------------------------------------------
ws_clients: list[WebSocket] = []


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.append(websocket)
    logger.info("WebSocket client connected (%d total)", len(ws_clients))
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"type": "pong", "data": data}))
    except WebSocketDisconnect:
        if websocket in ws_clients:
            ws_clients.remove(websocket)
        logger.info("WebSocket client disconnected (%d remaining)", len(ws_clients))


# ---------------------------------------------------------------------------
# Background vault watcher — monitors Needs_Action for new whatsapp files
# ---------------------------------------------------------------------------
_known_files: set[str] = set()


async def _vault_watcher_loop():
    """Poll vault/Needs_Action every 5 seconds for new whatsapp files, broadcast via WS."""
    vault_path = Path(settings.VAULT_PATH).resolve()
    needs_action = vault_path / "Needs_Action"

    # Seed known files — scan all whatsapp patterns including messages/ subfolder
    wa_patterns = ["whatsapp-*.md", "wa-msg-*.md", "wa-*.md"]
    if needs_action.exists():
        for pat in wa_patterns:
            for f in needs_action.glob(pat):
                _known_files.add(f.name)
            for f in needs_action.glob(f"**/{pat}"):
                _known_files.add(f.name)

    whatsapp.router  # ensure module loaded
    from app.routers.whatsapp import _sync_messages_from_vault, broadcast_ws, _all_messages
    import app.routers.whatsapp as wa_mod
    wa_mod._watcher_running = True

    logger.info("Vault watcher started — monitoring %s", needs_action)

    while True:
        try:
            if needs_action.exists():
                current: set[str] = set()
                for pat in wa_patterns:
                    for f in needs_action.glob(pat):
                        current.add(f.name)
                    for f in needs_action.glob(f"**/{pat}"):
                        current.add(f.name)
                new_files = current - _known_files
                for fname in sorted(new_files):
                    _known_files.add(fname)
                    _sync_messages_from_vault()
                    # Find the new message
                    for msg in wa_mod._vault_messages:
                        if msg.get("filename") == fname:
                            await broadcast_ws("whatsapp:message", msg)
                            logger.info("New WhatsApp message detected: %s", fname)
                            break
        except Exception as e:
            logger.error("Vault watcher error: %s", e)

        await asyncio.sleep(5)


# ---------------------------------------------------------------------------
# WhatsApp Web Watcher — runs Playwright-based scraper in background
# ---------------------------------------------------------------------------
async def _whatsapp_web_watcher_loop():
    """Run WhatsApp Web scraper every 60 seconds to fetch real messages."""
    import os
    import sys
    
    # Check if WhatsApp watcher is enabled
    if os.getenv("WA_WATCHER_ENABLED", "false").lower() not in ("true", "1", "yes"):
        logger.info("WhatsApp Web watcher disabled (set WA_WATCHER_ENABLED=true to enable)")
        return
    
    # Import watcher module
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    try:
        from whatsapp_watcher import run_poll, DRY_RUN, WA_HEADLESS
        from playwright.async_api import async_playwright
    except ImportError as e:
        logger.warning("WhatsApp watcher not available: %s", e)
        return
    
    logger.info("WhatsApp Web watcher started (DRY_RUN=%s, HEADLESS=%s)", DRY_RUN, WA_HEADLESS)

    # Persistent context directory
    profile_dir = Path(os.getenv("WA_PROFILE_DIR", Path(__file__).parent.parent.parent / ".whatsapp_profile")).resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Using WhatsApp profile: %s", profile_dir)

    # Outer retry loop — if browser crashes or QR times out, wait and try again
    while True:
        context = None
        try:
            async with async_playwright() as p:
                # Use persistent context (preserves WhatsApp Web login session)
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=WA_HEADLESS,
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                    viewport={"width": 1280, "height": 900},
                    locale="en-US",
                )

                pages = context.pages
                page = pages[0] if pages else await context.new_page()
                page.set_default_timeout(60_000)  # 60s timeout for slow connections

                # Navigate to WhatsApp Web
                try:
                    await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)
                    logger.info("WhatsApp Web loaded. Scan QR code if not already logged in.")
                except Exception as e:
                    logger.error("Failed to load WhatsApp Web: %s — will retry in 30s", e)
                    await context.close()
                    await asyncio.sleep(30)
                    continue  # retry outer loop

                # Wait for login (QR scan or existing session) — 5 minutes
                try:
                    await page.wait_for_selector(
                        'div[aria-label="Chat list"]',
                        timeout=300_000,  # 5 minutes for QR scan
                    )
                    logger.info("WhatsApp Web session active — chat list visible.")
                except Exception:
                    logger.warning("WhatsApp Web login timeout (5 min) — will retry in 30s")
                    await context.close()
                    await asyncio.sleep(30)
                    continue  # retry outer loop

                # Inner poll loop — runs while session is active
                while True:
                    try:
                        # Verify session is still active
                        chat_list = await page.query_selector('div[aria-label="Chat list"]')
                        if not chat_list:
                            logger.warning("WhatsApp session lost, attempting to reload...")
                            await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)
                            await asyncio.sleep(15)
                            continue

                        logger.info("Polling WhatsApp Web for unread messages...")
                        result = await run_poll(page)
                        logger.info(
                            "WhatsApp poll complete: processed=%d, skipped=%d, errors=%d",
                            result.get("processed", 0),
                            result.get("skipped", 0),
                            len(result.get("errors", []))
                        )
                    except Exception as e:
                        logger.error("WhatsApp watcher poll error: %s", e)
                        # If browser crashed, break inner loop to restart
                        if "Target closed" in str(e) or "Browser" in str(e):
                            logger.warning("Browser seems crashed — restarting watcher...")
                            break

                    # Wait 60 seconds before next poll
                    await asyncio.sleep(60)

        except Exception as e:
            logger.error("WhatsApp watcher crashed: %s — restarting in 30s", e)
        finally:
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

        # Wait before retrying
        await asyncio.sleep(30)


@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(_vault_watcher_loop())
    asyncio.create_task(_whatsapp_web_watcher_loop())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
