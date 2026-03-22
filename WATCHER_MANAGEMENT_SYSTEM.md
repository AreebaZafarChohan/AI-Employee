# Watcher Management System

Complete PM2-style process management for all AI Employee watchers and MCP servers.

## 🎯 Overview

This system provides a unified interface to monitor, start, stop, and restart all watchers from the frontend dashboard, similar to PM2 process management.

## 📋 Features

### Backend (`backend-python/app/services/watcher_service.py`)

- **Watcher Registry**: Centralized registry of all available watchers
- **Process Management**: Start, stop, restart individual or all watchers
- **Real-time Monitoring**: CPU, memory, uptime tracking
- **Log Aggregation**: Fetch recent logs from any watcher
- **State Persistence**: Watcher state survives restarts
- **Auto-discovery**: Detects which watchers are available based on script existence

### Frontend (`frontend/src/app/watchers/page.tsx`)

- **PM2-Style Dashboard**: Beautiful cards showing all watchers
- **Real-time Stats**: CPU, RAM, uptime, processed items
- **Live Logs**: View real-time logs for selected watcher
- **Filter & Search**: Filter by status (all, running, stopped, error)
- **Bulk Actions**: Start/Stop all watchers at once
- **Individual Control**: Start, stop, restart each watcher

## 🔧 Available Watchers

### Python Watchers

| ID | Name | Script | Description |
|----|------|--------|-------------|
| `gmail` | Gmail Watcher | `src/watcher/gmail_watcher.py` | Monitors Gmail for important emails |
| `whatsapp` | WhatsApp Watcher | `src/watcher/whatsapp_watcher.py` | Monitors WhatsApp messages |
| `linkedin` | LinkedIn Watcher | `src/watcher/linkedin_watcher.py` | Monitors LinkedIn DMs and mentions |
| `odoo` | Odoo Watcher | `src/watcher/odoo_watcher.py` | Monitors Odoo accounting events |
| `social` | Social Media Watcher | `src/watcher/social_watcher.py` | Monitors all social platforms |
| `bank` | Bank Watcher | `src/watcher/bank_watcher.py` | Monitors bank transactions |
| `vault` | Vault Watcher | `src/watcher/vault_watcher.py` | Monitors vault file changes |
| `webhook` | Webhook Receiver | `src/watcher/webhook_watcher.py` | Receives webhooks |
| `gmail-pubsub` | Gmail PubSub | `src/watcher/gmail_pubsub_watcher.py` | Gmail real-time notifications |
| `vault-rag` | Vault RAG Watcher | `src/watcher/vault_rag_watcher.py` | Processes vault for RAG |
| `ceo-briefing-weekly` | CEO Weekly Briefing | `monday_ceo_briefing.py` | Weekly CEO briefing generator |

### MCP Servers (Node.js)

| ID | Name | Script | Description |
|----|------|--------|-------------|
| `mcp-odoo` | MCP Odoo Server | `mcp/odoo-server/src/index.js` | Odoo integration |
| `mcp-email` | MCP Email Server | `mcp/email-server/src/index.js` | Email operations |
| `mcp-whatsapp` | MCP WhatsApp Server | `mcp/whatsapp-server/src/index.js` | WhatsApp integration |
| `mcp-linkedin` | MCP LinkedIn Server | `mcp/linkedin-server/src/index.js` | LinkedIn integration |
| `mcp-twitter` | MCP Twitter Server | `mcp/twitter-server/src/index.js` | Twitter integration |
| `mcp-watcher` | MCP Watcher Server | `mcp/watcher-server/src/index.js` | Watcher control |

### Social Media Watchers (Node.js)

| ID | Name | Script | Description |
|----|------|--------|-------------|
| `twitter` | Twitter Watcher | `mcp/twitter-server/src/index.js` | Monitors Twitter mentions |
| `facebook` | Facebook Watcher | `mcp/facebook-server/src/index.js` | Facebook page interactions |
| `instagram` | Instagram Watcher | `mcp/instagram-server/src/index.js` | Instagram DMs and comments |

## 🚀 API Endpoints

All endpoints are under `/api/v1/watchers`

### List All Watchers
```http
GET /api/v1/watchers
```

Returns status of all watchers with metrics.

### Get Service Summary
```http
GET /api/v1/watchers/summary
```

Returns aggregate statistics:
```json
{
  "total": 18,
  "running": 12,
  "stopped": 5,
  "error": 1,
  "total_logs": 6736,
  "total_processed": 1234,
  "health": "healthy"
}
```

### Get Specific Watcher
```http
GET /api/v1/watchers/{watcher_id}
```

### Start Watcher
```http
POST /api/v1/watchers/{watcher_id}/start
```

### Stop Watcher
```http
POST /api/v1/watchers/{watcher_id}/stop
```

### Restart Watcher
```http
POST /api/v1/watchers/{watcher_id}/restart
```

### Get Watcher Logs
```http
GET /api/v1/watchers/{watcher_id}/logs?limit=100
```

### Start All Watchers
```http
POST /api/v1/watchers/start-all
```

### Stop All Watchers
```http
POST /api/v1/watchers/stop-all
```

### List Watcher Registry
```http
GET /api/v1/watchers/registry/list
```

Returns the complete registry of all possible watchers (even if scripts don't exist).

## 📦 Installation

### Backend Dependencies

Install psutil for process monitoring:
```bash
cd backend-python
pip install -r requirements.txt
```

### Frontend

No additional dependencies needed. The frontend uses existing React Query hooks.

## 🎨 UI Features

### Dashboard Stats Cards
- **Active Watchers**: Shows running/total count
- **Logs Today**: Total log entries across all watchers
- **Items Processed**: Lifetime processed items
- **System Status**: Overall health indicator

### Watcher Cards
Each watcher card displays:
- **Icon & Color**: Unique identifier
- **Status Badge**: Online/Offline/Error with live indicator
- **Metrics**: CPU%, RAM, Uptime
- **Stats**: Items processed, logs today, PID
- **Last Log**: Most recent log entry
- **Actions**: Start/Stop/Restart buttons

### Live Logs Panel
- Click any watcher to view its logs
- Auto-refreshes every 5 seconds
- Color-coded by status (error=red, success=green)
- Scrollable history (last 50-100 entries)

## 🔐 Security

- All endpoints require authentication (add middleware as needed)
- Watchers can only execute scripts from predefined registry
- Process isolation via `start_new_session=True`
- State file stored in vault logs directory

##  State Management

Watcher state is persisted in:
```
AI-Employee-Vault/Logs/watcher_service_state.json
```

This file tracks:
- Watcher status (running/stopped/error)
- PID when running
- Restart count
- Started timestamp
- Error messages

## 🧪 Testing

### Test Backend Service

```python
# Test the watcher service directly
cd backend-python
python -c "
from app.services.watcher_service import get_watcher_service
service = get_watcher_service()

# List all watchers
watchers = service.list_watchers()
print(f'Total watchers: {len(watchers)}')

# Get summary
summary = service.get_service_summary()
print(f'Summary: {summary}')

# Start a watcher
result = service.start_watcher('gmail')
print(f'Start result: {result}')
"
```

### Test API Endpoints

```bash
# List watchers
curl http://localhost:8000/api/v1/watchers

# Get summary
curl http://localhost:8000/api/v1/watchers/summary

# Start gmail watcher
curl -X POST http://localhost:8000/api/v1/watchers/gmail/start

# Stop gmail watcher
curl -X POST http://localhost:8000/api/v1/watchers/gmail/stop

# Get logs
curl http://localhost:8000/api/v1/watchers/gmail/logs?limit=10
```

## 🐛 Troubleshooting

### Watcher Won't Start

1. **Check script exists**: Verify the script path in registry
2. **Check permissions**: Ensure script is executable
3. **Check dependencies**: Python/Node.js dependencies installed
4. **Check logs**: `AI-Employee-Vault/Logs/{watcher_id}.json`

### High CPU/Memory Usage

1. **Check logs**: Look for error loops
2. **Restart watcher**: Use restart button
3. **Reduce poll interval**: Adjust in watcher config
4. **Check external APIs**: Rate limits or slow responses

### State File Corruption

Delete the state file to reset:
```bash
rm AI-Employee-Vault/Logs/watcher_service_state.json
```

The service will auto-recreate it on next start.

## 🔄 Migration from run_master.py

The old `run_master.py` script can still be used, but the new system provides:
- **Better UI**: PM2-style dashboard vs terminal
- **Individual Control**: Start/stop specific watchers
- **Real-time Monitoring**: CPU, memory, uptime tracking
- **Log Aggregation**: Centralized log viewing
- **State Persistence**: Survives restarts
- **API Access**: Programmatic control

To migrate:
1. Stop `run_master.py` if running
2. Start backend server (watchers service auto-initializes)
3. Use frontend dashboard to start desired watchers

## 📝 Adding New Watchers

### 1. Add to Registry

Edit `backend-python/app/services/watcher_service.py`:

```python
WATCHER_REGISTRY = {
    # ... existing watchers ...
    "my-new-watcher": {
        "name": "My New Watcher",
        "script": "path/to/watcher.py",
        "command": [sys.executable, "path/to/watcher.py", "--watch"],
        "icon": "eye",  # Lucide icon name
        "color": "blue",  # Tailwind color
        "description": "What it does",
    },
}
```

### 2. Create Watcher Script

Ensure your watcher:
- Inherits from `BaseWatcher` (for Python)
- Supports `--watch` flag for continuous mode
- Logs to `AI-Employee-Vault/Logs/{watcher_id}.json`
- Writes to `Needs_Action/` when needed

### 3. Test

```bash
# Test script directly
python path/to/watcher.py --watch

# Test via API
curl -X POST http://localhost:8000/api/v1/watchers/my-new-watcher/start

# Check in UI
# Open http://localhost:3000/watchers
```

## 🎯 Best Practices

1. **Start Only Needed Watchers**: Don't run watchers for services you don't use
2. **Monitor Resource Usage**: Check CPU/RAM regularly
3. **Review Logs Daily**: Use live logs panel to spot issues
4. **Set Appropriate Poll Intervals**: Balance freshness vs resource usage
5. **Use Filters**: Filter by status to focus on problem watchers
6. **Restart Periodically**: Restart watchers weekly to prevent memory leaks

## 📚 Related Documentation

- [AGENTS.md](./AGENTS.md) - Agent coordination
- [APPROVAL_ORCHESTRATOR_GUIDE.md](./APPROVAL_ORCHESTRATOR_GUIDE.md) - Approval workflow
- [GOLD_TIER_README.md](./GOLD_TIER_README.md) - Gold tier features

## 🆘 Support

For issues or questions:
1. Check logs in `AI-Employee-Vault/Logs/`
2. Review watcher-specific logs (e.g., `gmail_watcher.json`)
3. Check system status in dashboard
4. Review error messages in UI

---

**Version**: 1.0.0  
**Last Updated**: 2026-03-19  
**Status**: Production Ready
