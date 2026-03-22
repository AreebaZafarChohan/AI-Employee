import os
import re
import yaml
from pathlib import Path
from datetime import datetime
from backend.config import get_settings

def parse_frontmatter(content: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        metadata = yaml.safe_load(match.group(1))
        return metadata or {}, match.group(2)
    except:
        return {}, content

def read_vault_folder(folder_name: str) -> list[dict]:
    settings = get_settings()
    # Resolve relative to backend/ root or absolute
    base_path = Path(settings.VAULT_PATH)
    if not base_path.is_absolute():
        # if settings says ../AI-Employee-Vault, it's relative to the backend/ folder
        base_path = (Path(__file__).parent.parent / settings.VAULT_PATH).resolve()
        
    folder = base_path / folder_name
    items = []
    if not folder.is_dir():
        return items
        
    files = sorted(folder.iterdir(), key=lambda x: x.stat().st_mtime if x.is_file() else 0, reverse=True)
    for f in files:
        if f.is_file() and f.suffix in (".md", ".txt"):
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                meta, body = parse_frontmatter(content)
                items.append({
                    "id": f.stem,
                    "filename": f.name,
                    "title": meta.get("title", f.stem),
                    "status": meta.get("status", folder_name.lower()),
                    "content": content,
                    "metadata": meta
                })
            except:
                continue
    return items
