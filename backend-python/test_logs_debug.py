#!/usr/bin/env python3
from app.services.audit_service import read_json_logs, get_unified_activity_logs
from app.config import settings
from pathlib import Path

vault = Path(settings.VAULT_PATH)
print(f"Vault: {vault}")

# Test read_json_logs
logs = read_json_logs(vault / "Logs", max_files=10)
print(f"\nread_json_logs found: {len(logs)} logs")
if logs:
    print(f"First log: {logs[0].get('source', 'no-source')} - {logs[0].get('action', 'no-action')}")

# Test unified logs
unified = get_unified_activity_logs(limit=10)
print(f"\nget_unified_activity_logs found: {len(unified)} logs")
if unified:
    for log in unified[:5]:
        print(f"  - {log.get('source')}: {log.get('action') or log.get('event_type')}")
