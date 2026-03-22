# ✅ WhatsApp Integration - Backend Integrated Version

## What Changed

The WhatsApp Web watcher now runs **inside the Python backend** as a background task. You only need to run **one command** instead of two separate processes!

## How to Run

### Single Command (Backend + WhatsApp Watcher)

```bash
cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee/backend-python
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

That's it! This starts:
1. ✅ FastAPI backend (port 8000)
2. ✅ Vault watcher (syncs files every 5 seconds)
3. ✅ WhatsApp Web watcher (polls every 60 seconds)

### Frontend (separate terminal)

```bash
cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee/frontend
npm run dev
```

Then open: `http://localhost:3000/whatsapp`

## Configuration (.env)

```bash
# Enable/disable WhatsApp watcher
WA_WATCHER_ENABLED=true

# Show browser UI (set false for headless/server mode)
WA_HEADLESS=false

# Persistent browser session (QR code saved here)
WA_PROFILE_DIR=.whatsapp_profile

# Don't write files (set false for real operation)
DRY_RUN=false

# Auto-send replies (set false to require approval)
WA_AUTO_REPLY=false
```

## What Happens on Startup

1. **Backend starts** → FastAPI listens on port 8000
2. **Vault watcher starts** → Monitors `Needs_Action/` folder
3. **WhatsApp watcher starts** → If `WA_WATCHER_ENABLED=true`:
   - Chromium browser launches
   - Opens WhatsApp Web
   - Shows QR code (first time only)
   - After QR scan, session saved in `.whatsapp_profile/`
   - Polls for unread messages every 60 seconds

## Logs to Watch For

```
INFO:     Started server process [25910]
INFO:     Application startup complete.
INFO:     Vault watcher started — monitoring /path/to/AI-Employee-Vault/Needs_Action
INFO:     WhatsApp Web watcher started (DRY_RUN=False, HEADLESS=False)
INFO:     WhatsApp Web loaded. Scan QR code if not already logged in.
INFO:     Polling WhatsApp Web for unread messages...
INFO:     WhatsApp poll complete: processed=2, skipped=0, errors=0
```

## Testing

1. **Start backend** (command above)
2. **Check browser opens** → Should see WhatsApp Web
3. **Scan QR code** → Only needed first time
4. **Send yourself a WhatsApp** → From another phone
5. **Wait 60 seconds** → Watcher polls every minute
6. **Check logs** → Should see "processed=1"
7. **Open frontend** → `http://localhost:3000/whatsapp`
8. **See real message** → No more fake sample data!

## Troubleshooting

### Browser doesn't open
- Check `WA_WATCHER_ENABLED=true` in `.env`
- Check `WA_HEADLESS=false` (or check logs for headless mode)

### QR code keeps showing
- Session not saving → Check `.whatsapp_profile/` exists
- Delete `.whatsapp_profile/` and restart to force fresh login

### No messages detected
- Send unread message to yourself from another number
- Check watcher logs: `AI-Employee-Vault/Logs/whatsapp-watcher-*.log`
- Verify `DRY_RUN=false` in `.env`

### Backend won't start
- Check syntax: `python3 -m py_compile app/main.py`
- Check imports: `pip install playwright && playwright install chromium`

## Files Modified

- `backend-python/app/main.py` - Added `_whatsapp_web_watcher_loop()`
- `.env` - Added `WA_WATCHER_ENABLED=true`
- `.env.example` - Added WhatsApp settings documentation
- `WHATSAPP_INTEGRATION_COMPLETE.md` - Updated with integrated instructions

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Python Backend (uvicorn)                       │
│  ┌─────────────────────────────────────────┐   │
│  │  FastAPI Server (port 8000)             │   │
│  │  - /api/v1/whatsapp/* endpoints         │   │
│  │  - WebSocket /ws                        │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │  Background Tasks (asyncio)             │   │
│  │  - Vault Watcher (5s interval)          │   │
│  │  - WhatsApp Web Watcher (60s interval)  │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
         │
         ├─→ Browser (Playwright) → WhatsApp Web
         │
         ├─→ Vault Files → Needs_Action/*.md
         │
         └─→ WebSocket → Frontend (React)
```

## Benefits

✅ **Simpler**: One command instead of two processes  
✅ **Reliable**: No need to coordinate separate watchers  
✅ **Efficient**: Shared event loop, no duplicate imports  
✅ **Better logging**: All logs in one place  
✅ **Easy deployment**: Single service to manage  

---

**Status:** ✅ Complete  
**Date:** 2026-03-18  
**Run Command:** `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
