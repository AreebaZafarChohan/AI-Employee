#!/usr/bin/env python3
from app.config import settings
from pathlib import Path

print(f"VAULT_PATH: {settings.VAULT_PATH}")
vault = Path(settings.VAULT_PATH)
print(f"Exists: {vault.exists()}")
print(f"Is dir: {vault.is_dir()}")

logs_dir = vault / "Logs"
print(f"\nLogs dir: {logs_dir}")
print(f"Exists: {logs_dir.exists()}")

if logs_dir.exists():
    files = list(logs_dir.iterdir())
    print(f"Files ({len(files)}):")
    for f in files[:10]:
        print(f"  - {f.name}")
