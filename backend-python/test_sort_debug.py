#!/usr/bin/env python3
from pathlib import Path
from app.config import settings

vault = Path(settings.VAULT_PATH)
logs_dir = vault / "Logs"

files = sorted(
    [f for f in logs_dir.iterdir() if f.suffix in (".json", ".log")],
    reverse=True,
)[:30]

print(f"Files to process: {len(files)}")
for f in files[:10]:
    print(f"  {f.name} ({f.suffix})")
