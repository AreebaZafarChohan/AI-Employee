"""Shared helpers for reading vault folders and parsing frontmatter."""

import os
import re
from pathlib import Path
from typing import Optional
from src.core.config import get_settings


import yaml

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and return (metadata, body)."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        # Try without body
        match_no_body = re.match(r"^---\s*\n(.*?)\n---\s*$", content, re.DOTALL)
        if match_no_body:
            try:
                metadata = yaml.safe_load(match_no_body.group(1))
                return metadata or {}, ""
            except:
                return {}, content
        return {}, content
    try:
        metadata = yaml.safe_load(match.group(1))
        return metadata or {}, match.group(2)
    except Exception:
        # Fallback to simple line parsing
        meta = {}
        for line in match.group(1).splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip().strip('"').strip("'")
        return meta, match.group(2)


def read_vault_folder(folder_name: str) -> list[dict]:
    """Read all markdown files from a vault subfolder, returning parsed items."""
    settings = get_settings()
    folder = Path(settings.VAULT_PATH) / folder_name
    items = []
    if not folder.is_dir():
        return items
    # Sort by mtime (newest first)
    files = sorted(folder.iterdir(), key=lambda x: x.stat().st_mtime if x.is_file() else 0, reverse=True)
    for f in files:
        if f.is_file() and f.suffix in (".md", ".txt"):
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                meta, body = parse_frontmatter(content)

                # Extract first 200 chars as preview
                preview = body.strip()[:200] + "..." if len(body.strip()) > 200 else body.strip()

                items.append({
                    "id": f.stem,
                    "filename": f.name,
                    "path": str(f),
                    "type": meta.get("type", meta.get("item_type", "unknown")),
                    "channel": meta.get("channel", meta.get("platform", "unknown")),
                    "title": meta.get("title", f.stem.replace("-", " ").replace("_", " ").title()),
                    "status": meta.get("status", folder_name.lower()),
                    "risk_level": meta.get("risk_level", "low"),
                    "createdAt": meta.get("created_at", meta.get("date", datetime.fromtimestamp(f.stat().st_ctime).isoformat())),
                    "body_preview": preview,
                    "metadata": meta,
                    "content": content,
                })
            except Exception as e:
                print(f"Error reading {f}: {e}")
                continue
    return items

from datetime import datetime



def move_vault_file(filename: str, from_folder: str, to_folder: str) -> Optional[str]:
    """Move a file between vault folders. Returns new path or None on failure."""
    settings = get_settings()
    src = Path(settings.VAULT_PATH) / from_folder / filename
    dst_dir = Path(settings.VAULT_PATH) / to_folder
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / filename
    if not src.is_file():
        return None
    src.rename(dst)
    return str(dst)
