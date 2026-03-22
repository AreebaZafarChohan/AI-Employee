import json
from pathlib import Path
from datetime import datetime, timezone
from app.config import settings

VAULT = Path(settings.VAULT_PATH)


def read_json_logs(directory: Path, max_files: int = 30) -> list[dict]:
    entries: list[dict] = []
    if not directory.is_dir():
        return entries

    # Process JSON and LOG files separately to ensure both are included
    json_files = sorted(
        [f for f in directory.iterdir() if f.suffix == ".json" and f.name != ".gitkeep"],
        reverse=True,
    )[:max_files // 2]  # Half for JSON
    
    log_files = sorted(
        [f for f in directory.iterdir() if f.suffix == ".log"],
        reverse=True,
    )[:max_files // 2]  # Half for LOG
    
    files = json_files + log_files

    for f in files:
        try:
            raw = f.read_text(encoding="utf-8").strip()
            if not raw:
                continue
                
            if f.suffix == ".json":
                # Try parsing as regular JSON first
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        entries.extend(parsed)
                    else:
                        entries.append(parsed)
                except json.JSONDecodeError:
                    # If that fails, try line-by-line (NDJSON format)
                    for line in raw.split("\n"):
                        line = line.strip()
                        if line:
                            try:
                                entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
            else:  # .log files
                for line in raw.split("\n"):
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            # Add source from filename
                            entry["source"] = f.stem
                            entries.append(entry)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            pass

    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries


def get_audit_logs(limit: int = 100, source: str = "all") -> list[dict]:
    entries: list[dict] = []
    if source in ("all", "audit"):
        entries.extend(read_json_logs(VAULT / "Audit"))
    if source in ("all", "logs"):
        entries.extend(read_json_logs(VAULT / "Logs"))
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


def get_unified_activity_logs(limit: int = 100) -> list[dict]:
    """
    Unified activity logs from all sources:
    - Gmail logs
    - WhatsApp logs
    - Vault Logs
    - Audit logs
    - Orchestrator actions
    - LEX decisions
    """
    entries: list[dict] = []
    
    # 1. Gmail Watcher logs
    gmail_log = VAULT / "Logs" / "gmail_watcher.json"
    if gmail_log.exists():
        entries.extend(read_json_logs(VAULT / "Logs", max_files=10))
    
    # 2. WhatsApp logs
    whatsapp_log = VAULT / "Logs" / "whatsapp_watcher.json"
    if whatsapp_log.exists():
        try:
            content = whatsapp_log.read_text(encoding="utf-8")
            for line in content.strip().split("\n"):
                if line.strip():
                    try:
                        entry = json.loads(line)
                        entry["source"] = "whatsapp"
                        entries.append(entry)
                    except:
                        pass
        except:
            pass
    
    # 3. Orchestrator actions
    orch_log = VAULT / "Logs" / "orchestrator-actions.json"
    if orch_log.exists():
        try:
            content = orch_log.read_text(encoding="utf-8")
            parsed = json.loads(content)
            if isinstance(parsed, list):
                for entry in parsed:
                    entry["source"] = "orchestrator"
                    entries.append(entry)
            else:
                parsed["source"] = "orchestrator"
                entries.append(parsed)
        except:
            pass
    
    # 4. LEX decisions
    lex_log = VAULT / "Logs" / "lex-decisions.json"
    if lex_log.exists():
        entries.extend(read_json_logs(VAULT / "Logs", max_files=5))
    
    # 5. System health logs
    health_logs = list((VAULT / "Logs").glob("system_health*"))
    for log_file in health_logs[:3]:
        try:
            content = log_file.read_text(encoding="utf-8")
            entries.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "system",
                "action": "health_check",
                "status": "success",
                "details": {"file": log_file.name}
            })
        except:
            pass
    
    # 6. Date-based logs (2026-03-12.json etc)
    entries.extend(read_json_logs(VAULT / "Logs", max_files=10))
    
    # Normalize and sort
    seen_ids = set()
    for entry in entries:
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        if "source" not in entry:
            entry["source"] = "system"
        if "id" not in entry:
            # Generate unique ID using timestamp + content hash
            import hashlib
            content = f"{entry['timestamp']}-{json.dumps(entry, sort_keys=True)}"
            unique_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            entry["id"] = f"log-{entry['timestamp'].replace(':', '').replace('.', '-')}-{unique_hash}"
        
        # Ensure ID uniqueness
        original_id = entry["id"]
        counter = 0
        while entry["id"] in seen_ids:
            counter += 1
            entry["id"] = f"{original_id}-{counter}"
        seen_ids.add(entry["id"])

    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]
