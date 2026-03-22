# Quick Start: Watcher Management System

## 🚀 Setup (5 minutes)

### Step 1: Install Backend Dependencies

```bash
cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee/backend-python
pip install -r requirements.txt
```

This installs `psutil` for process monitoring.

### Step 2: Start Backend Server

```bash
cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee/backend-python
python -m uvicorn app.main:app --reload --port 8000
```

Backend will start on `http://localhost:8000`

### Step 3: Start Frontend

```bash
cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee/frontend
npm run dev
```

Frontend will start on `http://localhost:3000`

### Step 4: Open Watchers Dashboard

Navigate to: **http://localhost:3000/watchers**

## 🎯 What You'll See

### Dashboard Stats (Top Row)
- **Active Watchers**: Shows how many are running (e.g., 6/18)
- **Logs Today**: Total log entries
- **Items Processed**: Lifetime count
- **System Status**: Overall health

### Watcher Cards Grid

Each card shows:
- ✅ **Green badge** = Running
- ⭕ **Gray badge** = Stopped  
- ❌ **Red badge** = Error

**Metrics displayed:**
- CPU %
- RAM (MB)
- Uptime (e.g., 2h 15m)
- Items processed
- Logs today
- PID

### Controls

**Top Action Bar:**
- 🟢 **Start All** - Starts all available watchers
- ⏹️ **Stop All** - Stops all running watchers
- 🔄 **Refresh** - Reloads status

**Filter Tabs:**
- All | Running | Stopped | Error

**Individual Watcher Actions:**
- ▶️ **Start** - Start a stopped watcher
- ⏹️ **Stop** - Stop a running watcher
- 🔄 **Restart** - Restart a watcher
- 📄 **Logs** - View live logs

### Live Logs Panel

Click any watcher card to see:
- Real-time log output
- Auto-refreshes every 5 seconds
- Color-coded (red=error, green=success)
- Scrollable history

## 📋 Common Tasks

### Start Gmail Watcher

1. Find "Gmail Watcher" card
2. Click **▶️ Start** button
3. Watch status change to "Online" (green)
4. Click card to view logs

### Stop WhatsApp Watcher

1. Find "WhatsApp Watcher" card
2. Click **⏹️ Stop** button
3. Status changes to "Offline" (gray)

### View Logs

1. Click any watcher card
2. Live logs panel appears at bottom
3. Shows last 50 log entries
4. Auto-refreshes every 5 seconds

### Start All Watchers

1. Click **🟢 Start All** button
2. Wait for all to start (watch status change)
3. Refresh if needed

### Filter by Status

1. Click "Running" tab to see only active watchers
2. Click "Error" tab to troubleshoot issues
3. Click "All" to see everything

## 🔧 Troubleshooting

### Watcher Won't Start

**Check if script exists:**
```bash
ls -la src/watcher/gmail_watcher.py
```

**Check logs:**
```bash
cat AI-Employee-Vault/Logs/gmail_watcher.json
```

**Test manually:**
```bash
python src/watcher/gmail_watcher.py --watch
```

### Backend Not Starting

**Install dependencies:**
```bash
cd backend-python
pip install -r requirements.txt
```

**Check port:**
```bash
netstat -an | grep 8000
```

### Frontend Not Loading

**Install node modules:**
```bash
cd frontend
npm install
```

**Check backend connection:**
- Open browser console (F12)
- Look for API errors
- Verify backend is running on port 8000

## 📊 API Testing

### Test with curl

```bash
# List all watchers
curl http://localhost:8000/api/v1/watchers

# Get summary
curl http://localhost:8000/api/v1/watchers/summary

# Start Gmail watcher
curl -X POST http://localhost:8000/api/v1/watchers/gmail/start

# Stop Gmail watcher
curl -X POST http://localhost:8000/api/v1/watchers/gmail/stop

# Get logs
curl http://localhost:8000/api/v1/watchers/gmail/logs?limit=10
```

### Test with Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# List watchers
response = requests.get(f"{BASE_URL}/watchers")
print(response.json())

# Start watcher
response = requests.post(f"{BASE_URL}/watchers/gmail/start")
print(response.json())

# Get status
response = requests.get(f"{BASE_URL}/watchers/gmail")
print(response.json())
```

## 🎨 UI Features Tour

### 1. Stats Cards (Top)
- Gradient backgrounds
- Real-time metrics
- Color-coded by metric type

### 2. Watcher Cards (Grid)
- Status indicator bar (top of card)
- Icon with brand colors
- Expandable on click
- Hover effects

### 3. Live Logs Panel
- Terminal-style dark theme
- Syntax highlighting
- Auto-scroll to bottom
- Timestamp display

### 4. Action Buttons
- Color-coded (green=start, red=stop)
- Loading states
- Disabled when inappropriate
- Tooltips on hover

## 📝 Available Watchers

### Python Watchers (`.py` scripts)
- 📧 Gmail Watcher
- 💬 WhatsApp Watcher
- 💼 LinkedIn Watcher
- 🛒 Odoo Watcher
- 🌐 Social Media Watcher
- 🏦 Bank Watcher
- 📁 Vault Watcher
- 🔗 Webhook Receiver
- 📬 Gmail PubSub
- 🧠 Vault RAG Watcher
- 📊 CEO Weekly Briefing

### Node.js Servers (`.js` scripts)
- 🖥️ MCP Odoo Server
- 🖥️ MCP Email Server
- 🖥️ MCP WhatsApp Server
- 🖥️ MCP LinkedIn Server
- 🖥️ MCP Twitter Server
- 🖥️ MCP Watcher Server
- 🐦 Twitter Watcher
- 📘 Facebook Watcher
- 📸 Instagram Watcher

## 🔐 Security Notes

- All API endpoints are protected (add auth middleware as needed)
- Watchers can only execute predefined scripts
- No arbitrary command execution
- State file is in vault directory
- Logs are append-only

## 📚 Next Steps

1. **Configure Watchers**: Set up environment variables in `.env`
2. **Test Individual Watchers**: Start one at a time
3. **Monitor Performance**: Watch CPU/RAM usage
4. **Set Up Alerts**: Configure error notifications
5. **Schedule Restarts**: Restart watchers periodically

## 🆘 Need Help?

**Check Logs:**
- `AI-Employee-Vault/Logs/watcher_service_state.json` - State
- `AI-Employee-Vault/Logs/{watcher_id}.json` - Watcher logs
- `AI-Employee-Vault/Logs/master-*.log` - Master runner logs

**Documentation:**
- [WATCHER_MANAGEMENT_SYSTEM.md](./WATCHER_MANAGEMENT_SYSTEM.md) - Full docs
- [AGENTS.md](./AGENTS.md) - Agent coordination
- [README.md](./README.md) - Project overview

---

**Happy Monitoring! 🎉**
