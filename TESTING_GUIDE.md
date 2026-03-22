# AI Employee Integration Testing Checklist

## 1. Backend Agent Reasoning
- [ ] Send natural language command to `CommandRouter`.
- [ ] Verify AI interprets intent correctly (social post vs email vs invoice).
- [ ] Verify structured Plan file is created in `/Vault/Plans/`.
- [ ] Verify platform-specific draft files are created in `/Vault/Pending_Approval/`.
- [ ] Verify draft metadata (YAML) contains all required fields for orchestrator.

## 2. API Endpoints
- [ ] `POST /api/v1/agent/command`: Returns 200 and plan ID.
- [ ] `GET /api/v1/tasks/pending`: Returns list of files from `/Vault/Pending_Approval/`.
- [ ] `GET /api/v1/tasks/needs-action`: Returns list of files from `/Vault/Needs_Action/`.
- [ ] `POST /api/v1/vault/approve`: Moves file from `Pending_Approval` to `Approved`.
- [ ] `POST /api/v1/vault/reject`: Moves file from `Pending_Approval` to `Rejected`.

## 3. Real-time Communication (WebSocket)
- [ ] Connect to `ws://localhost:8000/ws`.
- [ ] Send command from dashboard.
- [ ] Receive `draft_generated` event via WebSocket.
- [ ] Receive `approval_required` event via WebSocket.

## 4. Watcher to Agent Flow
- [ ] Drop a file in `/Vault/Inbox/`.
- [ ] Verify Watcher detects file and calls `POST /api/v1/events/new`.
- [ ] Verify Backend event queue picks up event.
- [ ] Verify Agent automatically creates a reply suggestion in `Pending_Approval`.

## 5. Execution (MCP)
- [ ] Move file to `Approved/`.
- [ ] Run `approval_orchestrator.py`.
- [ ] Verify MCP tool is called (check logs).
- [ ] Verify file is moved to `/Vault/Done/`.
- [ ] Verify execution log created in `/Vault/Logs/`.

---

# Testing Commands

### Python Requests (Automation)
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Send Command
resp = requests.post(f"{BASE_URL}/agent/command", json={
    "command": "Generate a Twitter post about AI integration"
})
print(resp.json())

# 2. Get Pending Approvals
resp = requests.get(f"{BASE_URL}/tasks/pending")
pending = resp.json()["data"]
if pending:
    filename = pending[0]["filename"]
    # 3. Approve
    requests.post(f"{BASE_URL}/vault/approve", json={"filename": filename})
```

### cURL (Manual)
```bash
# Send Command
curl -X POST http://localhost:8000/api/v1/agent/command \
     -H "Content-Type: application/json" \
     -d '{"command": "LinkedIn post about startups"}'

# List Pending
curl http://localhost:8000/api/v1/tasks/pending

# Approve
curl -X POST http://localhost:8000/api/v1/vault/approve \
     -H "Content-Type: application/json" \
     -d '{"filename": "POST_LINKEDIN_..."}'
```
