# Email MCP Server — Setup Complete ✅

## What's Done

### ✅ Step 1: DRY_RUN=false set
- File: `mcp/email-server/.env`
- `DRY_RUN=false` — Real emails will now be sent!

### ✅ Step 2: Claude Desktop Config Scripts Created
- **PowerShell**: `setup-claude-desktop.ps1`
- **Batch (Windows)**: `setup-windows.bat`

### ✅ Step 3: Documentation Updated
- README.md now includes complete setup instructions
- OAuth scope requirements documented

---

## How to Activate

### Option 1: Run the setup script (easiest)

```bash
# From project root
cd mcp/email-server
.\setup-windows.bat
```

Then **restart Claude Desktop**.

### Option 2: Manual setup

1. Open PowerShell and run:
   ```powershell
   .\setup-claude-desktop.ps1
   ```

2. Restart Claude Desktop

---

## Verify It Works

After restarting Claude Desktop, ask Claude:

```
What email tools do you have access to?
```

Claude should respond with:
- `send_email` — Send real emails
- `draft_email` — Create drafts
- `search_inbox` — Search Gmail

---

## ⚠️ Important: OAuth Scopes

Your current token has:
- ✅ `gmail.readonly`
- ✅ `gmail.modify`

For **full email sending**, you need:
- ❓ `gmail.send` — Required for `send_email`
- ❓ `gmail.compose` — Required for `draft_email`

### To add missing scopes:

1. Re-run the OAuth flow with additional scopes
2. Update `token.json`
3. Extract new refresh token:
   ```bash
   python3 -c "import json; t=json.load(open('token.json')); print(t['refresh_token'])"
   ```
4. Update `.env` with new refresh token

---

## Test Real Email Sending

Once Claude Desktop is configured:

```
Send a test email to test@example.com with subject "MCP Test" and body "Hello from MCP!"
```

If DRY_RUN=false and scopes are correct, the email will be sent!

---

## Files Created/Modified

| File | Status |
|------|--------|
| `mcp/email-server/.env` | ✅ Modified (DRY_RUN=false) |
| `mcp/email-server/setup-claude-desktop.ps1` | ✅ Created |
| `mcp/email-server/setup-windows.bat` | ✅ Created |
| `mcp/email-server/README.md` | ✅ Updated |
| `mcp/email-server/SETUP_COMPLETE.md` | ✅ This file |

---

## Next Steps

1. **Run** `.\setup-windows.bat` to configure Claude Desktop
2. **Restart** Claude Desktop
3. **Test** with a real email
4. **(If needed)** Re-authorize OAuth with `gmail.send` and `gmail.compose` scopes

---

**All 3 steps complete!** 🎉
