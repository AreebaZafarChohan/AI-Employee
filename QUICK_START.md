# AI Employee - Quick Start Reference Card

## 🚀 Start Everything (One Command)

### Windows
```cmd
start_all.bat
```
or
```cmd
python start_all.py start
```

### Linux/Mac
```bash
./start_all.sh
```
or
```bash
python start_all.py start
```

---

## 🎯 Essential Commands

| Command | Description |
|---------|-------------|
| `python start_all.py start` | Start all services |
| `python start_all.py stop` | Stop all services |
| `python start_all.py status` | Check service status |
| `python start_all.py restart` | Restart all services |

---

## 🌐 Access Points

| Service | URL | Port |
|---------|-----|------|
| Frontend | http://localhost:3000 | 3000 |
| Backend API | http://localhost:8000 | 8000 |
| API Docs | http://localhost:8000/docs | 8000 |

---

## 📝 Log Files Location

```
./logs/
├── backend.log
├── frontend.log
├── orchestrator.log
├── ai-agent.log
└── watcher-*.log
```

**View logs (real-time):**
```bash
# Windows PowerShell
Get-Content logs\backend.log -Wait

# Linux/Mac
tail -f logs/backend.log
```

---

## ⚡ Individual Service Start

```bash
# Backend only
cd backend && uvicorn main:app --reload

# Frontend only
cd frontend && npm run dev

# Watchers only
python run.py watcher gmail --watch

# Orchestrator only
python run.py orchestrator

# AI Agent only
python run.py agent
```

---

## 🛑 Stop Services

**Recommended:**
```bash
python start_all.py stop
```

**Manual (Windows):**
```cmd
taskkill /F /FI "WINDOWTITLE eq AI Employee*"
```

---

## ✅ Pre-Flight Checklist

Before starting, ensure:

- [ ] Python 3.8+ installed
- [ ] Node.js 20+ installed
- [ ] `.env` file created from `.env.example`
- [ ] Dependencies installed (`pip install -r requirements.txt`, `npm install`)
- [ ] Database configured (PostgreSQL or SQLite)
- [ ] API credentials in `.env`

---

## 🔧 Common Issues

| Issue | Solution |
|-------|----------|
| Port in use | `netstat -ano \| findstr :8000` then kill PID |
| Python not found | Add Python to PATH |
| .env missing | Copy `.env.example` to `.env` |
| Service won't start | Check logs in `./logs/` |

---

## 📞 Quick Help

```bash
# Show help
python start_all.py

# Check service status
python start_all.py status

# View logs
ls logs/
```

---

**Full Documentation:** [START_ALL_GUIDE.md](./START_ALL_GUIDE.md)
