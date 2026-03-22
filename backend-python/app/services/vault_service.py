import os
from pathlib import Path
from app.config import settings
from app.utils.markdown import parse_markdown

VAULT = Path(settings.VAULT_PATH)

FOLDER_MAP = {
    "needs_action": "Needs_Action",
    "pending": "Pending_Approval",
    "approved": "Approved",
    "rejected": "Rejected",
    "done": "Done",
}


def _determine_channel(metadata: dict, filename: str) -> str:
    if metadata.get("type") == "email" or metadata.get("source") == "gmail" or filename.startswith("email-"):
        return "gmail"
    if metadata.get("type") == "whatsapp" or metadata.get("source") == "whatsapp" or filename.startswith("whatsapp-"):
        return "whatsapp"
    if metadata.get("type") == "linkedin" or metadata.get("source") == "linkedin" or filename.startswith("linkedin-"):
        return "linkedin"
    if metadata.get("type") == "plan" or filename.startswith("plan-"):
        return "plan"
    return "general"


def get_folder_items(folder_key: str) -> list[dict]:
    folder_name = FOLDER_MAP.get(folder_key, folder_key)
    folder_path = VAULT / folder_name
    if not folder_path.is_dir():
        return []

    items = []
    for f in sorted(folder_path.iterdir(), reverse=True):
        if not f.suffix == ".md":
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        metadata, body = parse_markdown(content)
        stat = f.stat()
        channel = _determine_channel(metadata, f.name)
        items.append({
            "filename": f.name,
            "title": metadata.get("subject") or metadata.get("title") or f.stem,
            "status": folder_key,
            "channel": channel,
            "risk_level": (metadata.get("risk_level") or metadata.get("priority") or "medium").lower(),
            "created_at": metadata.get("created_at") or _iso(stat.st_ctime),
            "updated_at": _iso(stat.st_mtime),
            "metadata": metadata,
            "body_preview": body[:200].strip() + ("..." if len(body) > 200 else ""),
        })
    return items


def get_counts() -> dict[str, int]:
    counts = {}
    for key, folder_name in FOLDER_MAP.items():
        p = VAULT / folder_name
        counts[key] = len([f for f in p.iterdir() if f.suffix == ".md"]) if p.is_dir() else 0
    return counts


def move_file(filename: str, source_folders: list[str], dest_folder: str) -> str | None:
    """Move a file from one of source_folders to dest_folder. Returns new path or None."""
    for sf in source_folders:
        src = VAULT / sf / filename
        if src.is_file():
            dest_dir = VAULT / dest_folder
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / filename
            src.rename(dest)
            return str(dest)
    return None


def _iso(ts: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
