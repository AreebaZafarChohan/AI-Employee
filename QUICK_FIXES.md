# Quick Fixes for All Issues

## Issues Found

1. ✅ **Watchers API Working** - Returns all 18 watchers
2. ❌ **Gmail Token Expired** - Token from March 18, expired
3. ❌ **Frontend Not Loading Watchers** - Need to check why page shows "No watchers found"
4. ✅ **DRY_RUN=false** - Already set correctly

---

## Fix 1: Refresh Gmail Token

**Problem:** Token expired on March 18, 2026

**Solution:** Re-run OAuth setup

```bash
cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee
python setup_email_oauth.py
```

**Expected Output:**
```
[OK] Token refreshed successfully
[OK] Setup complete!
```

---

## Fix 2: WhatsApp Not Actually Sending

**Problem:** Message shows "sent successfully" but not received

**Root Cause:** The `/send` endpoint needs to explicitly pass `DRY_RUN=false` to sender script

**Status:** ✅ Already fixed in `backend-python/app/routers/whatsapp.py`

**To Apply Fix:** Restart backend

```bash
# Stop current backend (Ctrl+C)
cd backend-python
python -m uvicorn app.main:app --reload --port 8000
```

**Test:**
```bash
curl -X POST http://localhost:8000/api/v1/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "+923257011410",
    "message": "Test message",
    "dry_run": false
  }'
```

---

## Fix 3: Watchers Page Shows "No Watchers Found"

**Problem:** Frontend not loading watchers from API

**Diagnosis:** API returns data correctly ✅

**Possible Causes:**
1. Frontend not calling API
2. Network error
3. React component issue

**Debug Steps:**

1. **Open browser console** (F12) at `http://localhost:3000/watchers`
2. **Check for errors** in Console tab
3. **Check Network tab** for `/api/v1/watchers` request

**Quick Test:**
```bash
# Verify API is working
curl http://localhost:8000/api/v1/watchers | jq '.data | length'
# Should return: 18
```

**Frontend Fix:** Check `use-watchers.ts` hook

---

## Fix 4: Gmail Not Showing Emails

**Problem:** `Gmail service not initialized`

**Root Cause:** Expired token

**Solution:**

### Option A: Auto-refresh token
```bash
python setup_email_oauth.py
```

### Option B: Manual token refresh
```python
# In Python
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file("token.json")
creds.refresh(Request())
print(f"New expiry: {creds.expiry}")
```

### Option C: Delete and re-authorize
```bash
rm token.json
python setup_email_oauth.py
```

---

## Verification Checklist

After applying fixes:

### 1. Gmail Working
```bash
curl http://localhost:8000/api/v1/gmail/inbox?filter_type=all&limit=5
# Should return emails, not "service not initialized"
```

### 2. WhatsApp Sending
- Send message from frontend
- Check phone for actual message receipt
- Backend logs should show "Message sent successfully" (not DRY RUN)

### 3. Watchers Page
- Open `http://localhost:3000/watchers`
- Should see 18 watcher cards
- Click "Start All" to start watchers

---

## Current Status Summary

| Component | Status | Action Needed |
|-----------|--------|---------------|
| Watchers API | ✅ Working | None |
| Watchers Frontend | ⚠️ Not loading | Check console |
| Gmail Token | ❌ Expired | Re-run OAuth |
| WhatsApp Send | ⚠️ DRY_RUN | Restart backend |
| Emails Display | ❌ Not showing | Fix Gmail token |
| Draft Emails | ✅ Working | None |

---

## Immediate Action Plan

1. **Refresh Gmail token** (1 minute)
   ```bash
   python setup_email_oauth.py
   ```

2. **Restart backend** (30 seconds)
   ```bash
   cd backend-python
   # Ctrl+C, then:
   python -m uvicorn app.main:app --reload --port 8000
   ```

3. **Check watchers page** (1 minute)
   - Open `http://localhost:3000/watchers`
   - Open browser console (F12)
   - Look for errors

4. **Test WhatsApp send** (2 minutes)
   - Send test message
   - Verify actual receipt on phone

---

**Date:** 2026-03-19  
**Status:** Fixes identified, ready to apply
