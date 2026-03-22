#!/usr/bin/env python3
from pathlib import Path
from app.config import settings

vault = Path(settings.VAULT_PATH)
logs_dir = vault / "Logs"

# All files
all_files = list(logs_dir.iterdir())
print(f"All files: {len(all_files)}")

# JSON files only
json_files = [f for f in all_files if f.suffix == ".json"]
print(f"\nJSON files only: {len(json_files)}")
for f in json_files:
    print(f"  {f.name}")

# Filtered and sorted
filtered = sorted(
    [f for f in all_files if f.suffix in (".json", ".log")],
    reverse=True,
)
print(f"\nFiltered (.json + .log): {len(filtered)}")
for f in filtered[:15]:
    print(f"  {f.name}")
