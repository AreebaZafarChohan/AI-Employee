"""WhatsApp router — reads real messages from vault, sends via MCP, broadcasts via WebSocket."""

import asyncio
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from fastapi import APIRouter, Body, Query
from pydantic import BaseModel
from app.config import settings


class SendRequest(BaseModel):
    recipient: str
    message: str
    dry_run: bool = False


class ReceiveRequest(BaseModel):
    sender: str
    message: str
    risk_level: str = "medium"


class WatcherStartRequest(BaseModel):
    interval: int = 30
    dry_run: bool = False


router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
logger = logging.getLogger(__name__)

VAULT = Path(settings.VAULT_PATH).resolve()
NEEDS_ACTION = VAULT / "Needs_Action"
DONE = VAULT / "Done"
PENDING_APPROVAL = VAULT / "Pending_Approval"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_md_file(filepath: Path) -> Optional[dict]:
    """Parse a vault markdown file with YAML frontmatter."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    # Extract YAML frontmatter
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        return None

    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except Exception:
        meta = {}

    body = match.group(2).strip()
    return {
        "filename": filepath.name,
        "path": str(filepath),
        **meta,
        "body": body,
        "body_preview": body[:200],
    }


def _get_whatsapp_files(directory: Path) -> list[dict]:
    """Get all whatsapp-related files from a vault directory (including subfolders)."""
    if not directory.exists():
        return []
    items = []
    # Search multiple patterns and subfolders
    patterns = ["whatsapp-*.md", "wa-msg-*.md", "wa-*.md"]
    seen_paths: set[str] = set()
    for pattern in patterns:
        # Root level
        for f in directory.glob(pattern):
            if str(f) not in seen_paths:
                seen_paths.add(str(f))
                parsed = _parse_md_file(f)
                if parsed and parsed.get("source") == "whatsapp":
                    items.append(parsed)
        # Subfolders (messages/, whatsapp/, etc.)
        for f in directory.glob(f"**/{pattern}"):
            if str(f) not in seen_paths:
                seen_paths.add(str(f))
                parsed = _parse_md_file(f)
                if parsed and parsed.get("source") == "whatsapp":
                    items.append(parsed)
    # Also check any .md file in messages/ subfolder with source: whatsapp
    msgs_dir = directory / "messages"
    if msgs_dir.exists():
        for f in msgs_dir.glob("*.md"):
            if str(f) not in seen_paths:
                seen_paths.add(str(f))
                parsed = _parse_md_file(f)
                if parsed and parsed.get("source") == "whatsapp":
                    items.append(parsed)
    items.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return items


# ---------------------------------------------------------------------------
# In-memory message store (populated from vault + watcher)
# ---------------------------------------------------------------------------

_vault_messages: list[dict] = []
_api_messages: list[dict] = []
_watcher_running = False


def _sync_messages_from_vault():
    """Scan vault dirs and rebuild vault message list."""
    global _vault_messages
    seen_filenames: set[str] = set()
    all_msgs: list[dict] = []

    for directory, status in [
        (NEEDS_ACTION, "received"),
        (PENDING_APPROVAL, "pending"),
        (DONE, "processed"),
    ]:
        for item in _get_whatsapp_files(directory):
            if item["filename"] in seen_filenames:
                continue
            seen_filenames.add(item["filename"])
            all_msgs.append({
                "id": item["filename"].replace(".md", ""),
                "from": item.get("sender", "Unknown"),
                "to": "AI Employee",
                "content": item.get("message", item.get("body", item.get("body_preview", ""))),
                "timestamp": item.get("timestamp", item.get("received", item.get("created_at", datetime.now(timezone.utc).isoformat()))),
                "status": item.get("status", status),
                "type": item.get("type", "text"),
                "risk_level": item.get("risk_level", "medium"),
                "filename": item["filename"],
                "body": item.get("body", ""),
            })

    _vault_messages = all_msgs


def _all_messages() -> list[dict]:
    """Merge vault + API messages, newest first, deduplicated by id."""
    seen: set[str] = set()
    merged: list[dict] = []
    for m in _api_messages:
        if m["id"] not in seen:
            seen.add(m["id"])
            merged.append(m)
    for m in _vault_messages:
        if m["id"] not in seen:
            seen.add(m["id"])
            merged.append(m)
    return merged


# Initial sync
_sync_messages_from_vault()


# ---------------------------------------------------------------------------
# WebSocket broadcast helper (uses app.ws_clients from main.py)
# ---------------------------------------------------------------------------

async def broadcast_ws(event_type: str, data: dict):
    """Broadcast a message to all connected WebSocket clients."""
    from app.main import ws_clients
    msg = json.dumps({"type": event_type, "data": data})
    disconnected = []
    for ws in ws_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        ws_clients.remove(ws)


async def _queue_outbound_message(req: SendRequest, reason: str = "Queued for manual send") -> dict:
    """Save outbound message as a vault file so it can be sent later."""
    ts = datetime.now(timezone.utc)
    slug = re.sub(r"[^a-z0-9]", "-", req.recipient.lower())[:40]
    filename = f"whatsapp-outbound-{slug}-{ts.strftime('%Y%m%d%H%M%S')}.md"
    filepath = PENDING_APPROVAL / filename
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)

    content = f"""---
type: outbound
source: whatsapp
recipient: "{req.recipient}"
message: "{req.message}"
created_at: "{ts.isoformat()}"
status: pending
---

# Outbound WhatsApp Message

**To:** {req.recipient}
**Message:** {req.message}
**Reason:** {reason}
"""
    filepath.write_text(content, encoding="utf-8")

    new_msg = {
        "id": filename.replace(".md", ""),
        "from": "You",
        "to": req.recipient,
        "content": req.message,
        "timestamp": ts.isoformat(),
        "status": "pending",
        "type": "outbound",
        "risk_level": "low",
    }
    _api_messages.insert(0, new_msg)
    await broadcast_ws("whatsapp:queued", new_msg)

    return {"data": {"success": True, "queued": True, "message": reason}}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/messages")
async def get_messages(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
):
    _sync_messages_from_vault()
    msgs = _all_messages()
    if status:
        msgs = [m for m in msgs if m["status"] == status]
    total = len(msgs)
    start = (page - 1) * limit
    page_msgs = msgs[start : start + limit]
    return {
        "data": page_msgs,
        "meta": {"total": total, "page": page, "pageSize": limit},
    }


@router.get("/status")
async def get_status():
    _sync_messages_from_vault()
    all_msgs = _all_messages()
    received = sum(1 for m in all_msgs if m["status"] == "received")
    return {
        "data": {
            "connected": _watcher_running,
            "status": "active" if _watcher_running else "watching",
            "pendingMessages": received,
            "lastSync": datetime.now(timezone.utc).isoformat(),
            "totalMessages": len(all_msgs),
        }
    }


@router.post("/send")
async def send_message(req: SendRequest):
    """Send a WhatsApp message via whatsapp_sender.py, or queue in vault if unavailable."""
    try:
        root = Path(settings.VAULT_PATH).resolve().parent
        sender_script = root / "whatsapp_sender.py"
        if not sender_script.exists():
            # Fallback: save as pending outbound message in vault
            return await _queue_outbound_message(req)

        # whatsapp_sender.py uses --contact and --instruction flags
        cmd = [
            "python3", str(sender_script),
            "--contact", req.recipient,
            "--instruction", req.message,
        ]

        # Set up environment for subprocess
        env = os.environ.copy()
        
        # Load .env file to get DRY_RUN and other settings
        env_file = root / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env[key.strip()] = value.strip()
        
        # Override DRY_RUN based on request
        if req.dry_run:
            env["DRY_RUN"] = "true"
        else:
            env["DRY_RUN"] = "false"

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(root),
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        output = stdout.decode()
        error_output = stderr.decode()

        await broadcast_ws("whatsapp:sent", {
            "recipient": req.recipient,
            "message": req.message,
            "dry_run": req.dry_run,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "data": {
                "success": proc.returncode == 0,
                "output": output[:500] if output else "Message sent successfully",
                "error": error_output[:500] if proc.returncode != 0 else None,
            }
        }
    except asyncio.TimeoutError:
        # Sender timed out — queue in vault so user knows
        return await _queue_outbound_message(req, reason="Sender timed out — message queued for manual send")
    except Exception as e:
        return {"data": {"success": False, "error": str(e)}}


@router.post("/receive")
async def receive_message(req: ReceiveRequest):
    """Manually push a received message (used by watcher to notify backend)."""
    ts = datetime.now(timezone.utc)
    msg_id = f"whatsapp-{re.sub(r'[^a-z0-9]', '-', req.sender.lower())}-{ts.strftime('%Y%m%d%H%M%S')}"

    new_msg = {
        "id": msg_id,
        "from": req.sender,
        "to": "AI Employee",
        "content": req.message,
        "timestamp": ts.isoformat(),
        "status": "received",
        "type": "text",
        "risk_level": req.risk_level,
    }
    _api_messages.insert(0, new_msg)

    # Broadcast to all WS clients
    await broadcast_ws("whatsapp:message", new_msg)

    return {"data": new_msg}


@router.get("/contacts")
async def get_contacts():
    """Get list of contacts from vault WhatsApp messages."""
    _sync_messages_from_vault()
    msgs = _all_messages()
    
    # Extract unique contacts
    contacts_dict = {}
    for msg in msgs:
        sender = msg.get("from", "Unknown")
        if sender not in contacts_dict:
            contacts_dict[sender] = {
                "name": sender,
                "number": "",  # Would need to be mapped from a contacts file
                "lastMessageTime": msg.get("timestamp", ""),
                "unreadCount": 1 if msg.get("status") == "received" else 0,
            }
        else:
            if msg.get("status") == "received":
                contacts_dict[sender]["unreadCount"] += 1
    
    contacts = list(contacts_dict.values())
    
    # Normalize lastMessageTime to string for sorting
    def normalize_time(value):
        if not value:
            return ""
        if isinstance(value, str):
            return value
        # Handle datetime objects
        try:
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)
        except Exception:
            return str(value)
    
    contacts.sort(key=lambda c: normalize_time(c.get("lastMessageTime", "")), reverse=True)

    return {"data": contacts}


@router.get("/pending")
async def get_pending_messages():
    """Get messages pending approval (drafted by agent)."""
    _sync_messages_from_vault()
    msgs = _all_messages()
    
    # Filter for pending messages (agent-drafted replies)
    pending = [m for m in msgs if m.get("status") == "pending"]
    
    return {"data": pending}


@router.post("/approve")
async def approve_message(req: dict = Body()):
    """Approve and send a pending message."""
    message_id = req.get("message_id")
    reply_content = req.get("reply_content", "")
    
    # Find the message
    _sync_messages_from_vault()
    msgs = _all_messages()
    msg = next((m for m in msgs if m.get("id") == message_id), None)
    
    if not msg:
        return {"data": {"success": False, "error": "Message not found"}}
    
    # Send the message via MCP
    try:
        root = Path(settings.VAULT_PATH).resolve().parent
        sender_script = root / "whatsapp_sender.py"
        if not sender_script.exists():
            return {"data": {"success": False, "error": "whatsapp_sender.py not found"}}

        # Load environment from project .env
        env_file = root / ".env"
        env_vars = os.environ.copy()
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        
        # Ensure DRY_RUN is false for actual sending
        env_vars["DRY_RUN"] = "false"

        cmd = [
            "python3", str(sender_script),
            "--recipient", msg.get("from", ""),
            "--message", reply_content,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(root),
            env=env_vars,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        output = stdout.decode()

        # Update message status
        msg["status"] = "sent"
        
        await broadcast_ws("whatsapp:approved", {
            "message_id": message_id,
            "recipient": msg.get("from"),
            "reply": reply_content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "data": {
                "success": proc.returncode == 0,
                "output": output[:500],
            }
        }
    except Exception as e:
        return {"data": {"success": False, "error": str(e)}}


@router.post("/reject")
async def reject_message(req: dict = Body()):
    """Reject a pending message."""
    message_id = req.get("message_id")
    reason = req.get("reason", "")
    
    # Find and remove the message
    global _api_messages
    _api_messages = [m for m in _api_messages if m.get("id") != message_id]
    
    await broadcast_ws("whatsapp:rejected", {
        "message_id": message_id,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    
    return {"data": {"success": True}}
