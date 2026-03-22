from fastapi import APIRouter, Query
from backend.api.response import api_response
from pathlib import Path
import json
from datetime import datetime

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

LOGS_DIR = Path("./logs")

@router.get("")
async def get_audit_logs(limit: int = Query(50, ge=1, le=500)):
    """Get recent audit logs"""
    logs = []
    
    # Read orchestrator actions log
    orch_log = LOGS_DIR / "orchestrator-actions.json"
    if orch_log.exists():
        try:
            with open(orch_log, 'r') as f:
                content = f.read().strip()
                if content:
                    # Try to parse as JSON array or line-by-line JSON
                    try:
                        orch_logs = json.loads(content)
                        if isinstance(orch_logs, list):
                            logs.extend(orch_logs[-limit:])
                        else:
                            logs.append(orch_logs)
                    except json.JSONDecodeError:
                        # Try line-by-line
                        for line in content.split('\n')[-limit:]:
                            if line.strip():
                                try:
                                    logs.append(json.loads(line))
                                except:
                                    logs.append({"raw": line})
        except Exception as e:
            logs.append({"error": f"Failed to read orchestrator log: {str(e)}"})
    
    # Read lex decisions log
    lex_log = LOGS_DIR / "lex-decisions.json"
    if lex_log.exists():
        try:
            with open(lex_log, 'r') as f:
                content = f.read().strip()
                if content:
                    try:
                        lex_logs = json.loads(content)
                        if isinstance(lex_logs, list):
                            logs.extend(lex_logs[-limit:])
                        else:
                            logs.append(lex_logs)
                    except json.JSONDecodeError:
                        for line in content.split('\n')[-limit:]:
                            if line.strip():
                                try:
                                    logs.append(json.loads(line))
                                except:
                                    logs.append({"raw": line})
        except Exception as e:
            logs.append({"error": f"Failed to read lex log: {str(e)}"})
    
    # Sort by timestamp if available
    logs.sort(
        key=lambda x: x.get("timestamp", "") if isinstance(x, dict) else "",
        reverse=True
    )
    
    return api_response({
        "logs": logs[:limit],
        "total": len(logs),
        "limit": limit
    })

@router.get("/watcher-logs")
async def get_watcher_logs(watcher: str = Query(None), limit: int = 50):
    """Get watcher-specific logs"""
    watcher_files = {
        "gmail": "watcher-gmail.json",
        "whatsapp": "watcher-whats.json",
        "finance": "watcher-finance.json",
        "filesystem": "watcher-fs.json"
    }
    
    logs = []
    
    if watcher and watcher in watcher_files:
        log_file = LOGS_DIR / watcher_files[watcher]
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        try:
                            watcher_logs = json.loads(content)
                            if isinstance(watcher_logs, list):
                                logs = watcher_logs[-limit:]
                            else:
                                logs = [watcher_logs]
                        except json.JSONDecodeError:
                            for line in content.split('\n')[-limit:]:
                                if line.strip():
                                    try:
                                        logs.append(json.loads(line))
                                    except:
                                        logs.append({"raw": line})
            except Exception as e:
                logs.append({"error": str(e)})
    else:
        # Return all watcher logs
        for watcher_name, filename in watcher_files.items():
            log_file = LOGS_DIR / filename
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        content = f.read().strip()
                        if content:
                            try:
                                watcher_logs = json.loads(content)
                                if isinstance(watcher_logs, list):
                                    for log in watcher_logs[-10:]:
                                        log["watcher"] = watcher_name
                                        logs.append(log)
                                else:
                                    watcher_logs["watcher"] = watcher_name
                                    logs.append(watcher_logs)
                            except:
                                pass
                except:
                    pass
    
    return api_response({
        "logs": logs,
        "watcher": watcher or "all"
    })
