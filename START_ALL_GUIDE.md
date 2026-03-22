# AI Employee - Start All Services Guide

This document explains how to use the `start_all` scripts to run the entire AI Employee system.

---

## 📁 Available Scripts

| Script | Platform | Usage |
|--------|----------|-------|
| `start_all.bat` | Windows | Double-click or run in CMD |
| `start_all.sh` | Linux/Mac | `./start_all.sh` |
| `start_all.py` | Cross-platform | `python start_all.py start` |

---

## 🚀 Quick Start (Windows)

### Option 1: Batch File (Easiest)
```cmd
start_all.bat
```
Simply double-click `start_all.bat` or run it from Command Prompt.

### Option 2: Python Script (Recommended)
```cmd
python start_all.py start
```

---

## 🎯 Commands (Python Script)

The Python script provides the most control:

### Start All Services
```bash
python start_all.py start
```

### Stop All Services
```bash
python start_all.py stop
```

### Check Status
```bash
python start_all.py status
```

### Restart All Services
```bash
python start_all.py restart
```

---

## 📋 What Gets Started

When you run `start_all`, the following services are launched:

| # | Service | Port | Description |
|---|---------|------|-------------|
| 1 | **Backend API** | 8000 | FastAPI server handling all API requests |
| 2 | **Frontend** | 3000 | Next.js web application |
| 3 | **Gmail Watcher** | - | Monitors Gmail inbox for new emails |
| 4 | **LinkedIn Watcher** | - | Monitors LinkedIn for messages and mentions |
| 5 | **WhatsApp Watcher** | - | Monitors WhatsApp messages |
| 6 | **Orchestrator** | - | Manages task lifecycle (Inbox → Plans → Done) |
| 7 | **AI Agent** | - | Ralph reasoning loop for decision making |

---

## 📊 Access URLs

Once started, access the services at:

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 📝 Log Files

All services write logs to the `./logs/` directory:

```
logs/
├── backend.log
├── frontend.log
├── watcher-gmail.log
├── watcher-linkedin.log
├── watcher-whatsapp.log
├── orchestrator.log
├── ai-agent.log
└── pids/           # PID files for process management
```

### View Logs (Real-time)

**Windows (PowerShell):**
```powershell
Get-Content logs\backend.log -Wait -Tail 50
```

**Linux/Mac:**
```bash
tail -f logs/backend.log
```

---

## ⚠️ Prerequisites

Before running `start_all`, ensure you have:

### Required Software
- **Python 3.8+** (add to PATH)
- **Node.js 20+** (add to PATH)
- **Git** (for version control)

### Required Configuration
- **`.env` file** (create from `.env.example`)
- **API credentials** (Gmail, LinkedIn, etc.)
- **Database** (PostgreSQL or SQLite for development)

### Install Dependencies

**Python:**
```bash
pip install -r requirements.txt
```

**Node.js:**
```bash
npm install
```

---

## 🛑 Stopping Services

### Method 1: Python Script (Recommended)
```bash
python start_all.py stop
```

### Method 2: Manual (Batch/Shell Scripts)
Close each terminal window that opened for the services.

### Method 3: Force Stop (Windows)
```cmd
taskkill /F /FI "WINDOWTITLE eq AI Employee*"
```

---

## 🔧 Troubleshooting

### Port Already in Use
**Error:** `Address already in use` or `EADDRINUSE`

**Solution:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /F /PID <PID>

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Python Not Found
**Error:** `Python is not installed or not in PATH`

**Solution:**
1. Install Python 3.8+ from python.org
2. Add Python to PATH during installation
3. Restart terminal/CMD

### Node.js Not Found
**Error:** `Node.js is not installed or not in PATH`

**Solution:**
1. Install Node.js 20+ from nodejs.org
2. Add Node.js to PATH
3. Restart terminal/CMD

### .env File Missing
**Warning:** `.env file not found`

**Solution:**
```bash
cp .env.example .env
# Edit .env with your API credentials
```

### Service Won't Start
Check the corresponding log file:
```bash
# View last 50 lines
tail -f logs/<service>.log
```

---

## 🎛️ Advanced Usage

### Start Individual Services

If you only need specific services:

**Backend Only:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend Only:**
```bash
cd frontend
npm run dev
```

**Watchers Only:**
```bash
python run.py watcher gmail --watch
python run.py watcher linkedin --watch
python run.py watcher whatsapp --watch
```

**Orchestrator Only:**
```bash
python run.py orchestrator
```

**AI Agent Only:**
```bash
python run.py agent
```

---

## 📊 Service Dependencies

```
start_all
├── Backend API (FastAPI)
│   └── Database (PostgreSQL/SQLite)
│
├── Frontend (Next.js)
│   └── Backend API (must be running)
│
├── Watchers
│   ├── Gmail Watcher → Gmail API
│   ├── LinkedIn Watcher → LinkedIn API
│   └── WhatsApp Watcher → WhatsApp Web
│
├── Orchestrator
│   └── Backend API (for task management)
│
└── AI Agent (Ralph Loop)
    └── Backend API (for reasoning)
```

---

## 🔄 Auto-Restart on Failure

Services are configured to auto-restart on failure:
- **Backend**: Auto-restarts via `--reload` flag
- **Frontend**: Auto-restarts via Next.js dev server
- **Watchers/Agent**: Auto-restart via orchestrator

For production deployment, consider using:
- **PM2** (Node.js process manager)
- **Supervisor** (Python process manager)
- **Docker** (container orchestration)

---

## 📚 Related Documentation

- [README.md](./README.md) - Project overview
- [AGENTS.md](./AGENTS.md) - Agent coordination protocol
- [APPROVAL_ORCHESTRATOR_GUIDE.md](./APPROVAL_ORCHESTRATOR_GUIDE.md) - Approval workflow
- [backend/README.md](./backend/README.md) - Backend API documentation
- [frontend/README.md](./frontend/README.md) - Frontend documentation

---

## 🆘 Need Help?

If you encounter issues:

1. **Check logs** in `./logs/` directory
2. **Verify prerequisites** are installed
3. **Ensure .env file** is properly configured
4. **Check port availability** (8000, 3000)
5. **Review error messages** in terminal output

For additional support, check the project's issue tracker or documentation.

---

**Version:** 1.0.0  
**Last Updated:** 2026-03-16
