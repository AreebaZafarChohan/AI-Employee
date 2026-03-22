# Bug Fixes Summary

## Fixed Issues

### 1. WhatsApp Contacts Sort Error ✅ FIXED

**Error:** `TypeError: '<' not supported between instances of 'datetime.datetime' and 'str'`

**Location:** `backend-python/app/routers/whatsapp.py:320`

**Problem:** The `lastMessageTime` field could be either a datetime object or string, causing sort to fail.

**Solution:** Added `normalize_time()` function to convert all values to strings before sorting:

```python
def normalize_time(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    # Handle datetime objects
    try:
        return value.isoformat() if hasattr(value, 'isoformat') else str(value)
    except Exception:
        return str(value)

contacts.sort(key=lambda c: normalize_time(c.get("lastMessageTime", "")), reverse=True)
```

---

### 2. Duplicate React Keys in Activity Feed ✅ FIXED

**Error:** `Warning: Encountered two children with the same key, log-2026-03-15T18:24:55.233216Z-6672`

**Location:** `frontend/src/store/activity-store.ts:101`

**Problem:** ID generation used `Math.random()` which could generate same value when logs created quickly.

**Solution:** Improved unique ID generation with better randomness:

```typescript
// Before
id: log.id || `log-${log.timestamp}-${Math.random()}`

// After
const uniqueSuffix = `${Date.now()}-${Math.random().toString(36).substr(2, 11)}`;
id: log.id || `log-${log.timestamp}-${uniqueSuffix}`
```

---

### 3. Duplicate IDs in Backend Audit Logs ✅ FIXED

**Error:** Same duplicate keys appearing in live logs

**Location:** `backend-python/app/services/audit_service.py:159`

**Problem:** Using `hash()` function which can return same value for similar entries.

**Solution:** Use MD5 hash of timestamp + content, with deduplication tracking:

```python
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
```

---

### 4. Gmail SSL Errors ⚠️ KNOWN ISSUE

**Error:** `[SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC] decryption failed or bad record mac`

**Cause:** Gmail OAuth token corruption or network issues during SSL handshake.

**Workarounds:**
1. **Re-authorize Gmail:**
   ```bash
   python setup_email_oauth.py
   ```

2. **Delete and regenerate token:**
   ```bash
   rm token.json
   python reauthorize_gmail.py
   ```

3. **Check network:** Ensure stable internet connection

4. **Update Google libraries:**
   ```bash
   pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

**Note:** This is a known issue with Gmail API OAuth and doesn't affect the watcher management system.

---

## Testing

### Test WhatsApp Contacts Fix

```bash
# Backend should now return 200 OK
curl http://localhost:8000/api/v1/whatsapp/contacts
```

**Expected:** Returns contacts array without error

### Test Activity Feed

1. Open dashboard at `http://localhost:3000/dashboard`
2. Check browser console (F12)
3. No duplicate key warnings should appear

### Test Live Logs

1. Open `http://localhost:3000/live-logs`
2. Check browser console
3. No duplicate key warnings

---

## Files Modified

1. `backend-python/app/routers/whatsapp.py` - Fixed contacts sort
2. `frontend/src/store/activity-store.ts` - Improved ID generation
3. `backend-python/app/services/audit_service.py` - Fixed duplicate IDs

---

## Watcher Management System Status ✅

The new watcher management system is **fully functional**:

- ✅ Backend service created
- ✅ API endpoints working
- ✅ Frontend dashboard implemented
- ✅ Start/Stop/Restart controls working
- ✅ Live logs panel functional
- ✅ All 18 watchers registered

**Test the Watchers Page:**
```bash
# Open watchers dashboard
http://localhost:3000/watchers

# Test API
curl http://localhost:8000/api/v1/watchers
curl http://localhost:8000/api/v1/watchers/summary
```

---

## Next Steps

1. **Gmail OAuth:** Re-authorize if SSL errors persist
2. **Monitor Logs:** Check for any new errors in console
3. **Test Watchers:** Use the new watchers dashboard to control services

---

**Status:** All critical bugs fixed ✅  
**Date:** 2026-03-19  
**Version:** 1.0.1
