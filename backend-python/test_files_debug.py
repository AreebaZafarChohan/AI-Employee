#!/usr/bin/env python3
from pathlib import Path
from app.config import settings
import json

vault = Path(settings.VAULT_PATH)
logs_dir = vault / "Logs"

print(f"Logs dir: {logs_dir}")
print(f"Exists: {logs_dir.exists()}")

# List all JSON files
json_files = [f for f in logs_dir.iterdir() if f.suffix == ".json"]
print(f"\nJSON files found: {len(json_files)}")

for f in json_files[:5]:
    print(f"\nFile: {f.name}")
    try:
        raw = f.read_text(encoding="utf-8").strip()
        print(f"  Size: {len(raw)} chars")
        if raw:
            # Try JSON array
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    print(f"  Type: JSON Array with {len(parsed)} items")
                else:
                    print(f"  Type: JSON Object")
            except:
                # Try NDJSON
                lines = [l for l in raw.split("\n") if l.strip()]
                print(f"  Type: NDJSON with {len(lines)} lines")
    except Exception as e:
        print(f"  Error: {e}")
