#!/usr/bin/env python3
from app.services import audit_service

logs = audit_service.get_unified_activity_logs(limit=5)
print(f"Found {len(logs)} logs")
if logs:
    for log in logs[:3]:
        print(f"  - {log.get('source')}: {log.get('action') or log.get('event_type')}")
