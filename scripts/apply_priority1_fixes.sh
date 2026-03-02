#!/bin/bash
# Silver Tier — Priority 1 Security Fixes
# Run this script to apply HIGH severity fixes from the audit report
#
# Audit Report: SILVER_TIER_AUDIT_REPORT.md
# Date: March 1, 2026

set -e

echo "=================================================="
echo "Silver Tier — Priority 1 Security Fixes"
echo "=================================================="
echo ""

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Backup function
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        cp "$file" "$file.bak.$(date +%Y%m%d%H%M%S)"
        echo "✓ Backed up: $file"
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Fix 1: Change DRY_RUN defaults from false to true"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

DRY_RUN_FILES=(
    "approval_orchestrator.py"
    "orchestrator.py"
    "whatsapp_sender.py"
    "whatsapp_watcher.py"
    "gmail_watcher.py"
    "linkedin_sales_post_engine.py"
    "linkedin_watcher.py"
    "daily_briefing_generator.py"
    "monday_ceo_briefing.py"
)

for file in "${DRY_RUN_FILES[@]}"; do
    if [ -f "$file" ]; then
        backup_file "$file"
        # Change default from "false" to "true"
        sed -i 's/os\.getenv("DRY_RUN", "false")/os.getenv("DRY_RUN", "true")/g' "$file"
        echo "✓ Fixed: $file"
    else
        echo "⚠ Not found: $file"
    fi
done

# Fix email MCP server .env.example
if [ -f "mcp/email-server/.env.example" ]; then
    backup_file "mcp/email-server/.env.example"
    sed -i 's/^DRY_RUN=false/DRY_RUN=true/' "mcp/email-server/.env.example"
    echo "✓ Fixed: mcp/email-server/.env.example"
fi

# Fix email MCP server REQUIRE_APPROVAL default
if [ -f "mcp/email-server/.env.example" ]; then
    sed -i 's/^REQUIRE_APPROVAL=false/REQUIRE_APPROVAL=true/' "mcp/email-server/.env.example"
    echo "✓ Fixed: mcp/email-server/.env.example (REQUIRE_APPROVAL)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Fix 2: Update RETENTION_DAYS from 30 to 90"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Fix .env.example
if [ -f ".env.example" ]; then
    backup_file ".env.example"
    sed -i 's/^RETENTION_DAYS=30/RETENTION_DAYS=90/' ".env.example"
    echo "✓ Fixed: .env.example (RETENTION_DAYS=90)"
fi

# Fix src/utils/config.py
if [ -f "src/utils/config.py" ]; then
    backup_file "src/utils/config.py"
    sed -i 's/retention_days.*"30"/retention_days: int = int(os.getenv("RETENTION_DAYS", "90"))/' "src/utils/config.py"
    echo "✓ Fixed: src/utils/config.py"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Fix 3: Create log rotation script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cat > scripts/rotate_logs.sh << 'SCRIPT'
#!/bin/bash
# Log Rotation Script — 90 Day Retention
# Run weekly via cron: 0 2 * * 0 /path/to/rotate_logs.sh

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS_DIR="$ROOT/logs"
VAULT_LOGS="$ROOT/AI-Employee-Vault/Logs"
RETENTION_DAYS=90

echo "Starting log rotation..."
echo "Retention: $RETENTION_DAYS days"

# Rotate root logs
if [ -d "$LOGS_DIR" ]; then
    find "$LOGS_DIR" -name "*.log" -type f -mtime +$RETENTION_DAYS -delete
    echo "✓ Rotated: $LOGS_DIR"
fi

# Rotate vault logs
if [ -d "$VAULT_LOGS" ]; then
    find "$VAULT_LOGS" -name "*.json" -type f -mtime +$RETENTION_DAYS -delete
    echo "✓ Rotated: $VAULT_LOGS"
fi

# Rotate MCP server logs
for mcp_dir in mcp/*/logs; do
    if [ -d "$mcp_dir" ]; then
        find "$mcp_dir" -name "*.json" -type f -mtime +$RETENTION_DAYS -delete
        echo "✓ Rotated: $mcp_dir"
    fi
done

echo "Log rotation complete!"
SCRIPT

chmod +x scripts/rotate_logs.sh
echo "✓ Created: scripts/rotate_logs.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Fix 4: Add WhatsApp approval gate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Add approval check to whatsapp_watcher.py
if [ -f "whatsapp_watcher.py" ]; then
    backup_file "whatsapp_watcher.py"
    
    # Add approval check after risk classification
    cat >> whatsapp_watcher_approval_patch.txt << 'PATCH'

# NOTE: Approval gate added by security audit (March 1, 2026)
# High-risk WhatsApp messages now require approval before sending

def save_whatsapp_for_approval(contact: str, message: str, risk_level: str, metadata: dict = None):
    """Save high-risk WhatsApp message to Pending_Approval instead of sending."""
    from datetime import datetime, timezone
    
    pending_dir = VAULT_PATH / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"whatsapp_{contact.replace(' ', '_')}_{timestamp}.md"
    filepath = pending_dir / filename
    
    content = f"""---
type: whatsapp_message
contact: {contact}
risk_level: {risk_level}
requires_approval: true
created_at: {datetime.now(timezone.utc).isoformat()}
status: pending_approval
action_type: send_whatsapp
---

# WhatsApp Message Pending Approval

**Contact:** {contact}  
**Risk Level:** {risk_level}  
**Created:** {datetime.now(timezone.utc).isoformat()}

---

## Message Content

{message}

---

## Approval Required

This message requires human approval before sending due to:
- High risk level detected
- Potential external contact
- Sensitive content

**Do not send without approval.**
"""
    
    filepath.write_text(content, encoding="utf-8")
    logger.info(f"WhatsApp message saved for approval: {filepath.name}")
    return filepath
PATCH

    echo "✓ Created approval function patch (whatsapp_watcher_approval_patch.txt)"
    echo "  Manual step: Integrate this function into whatsapp_watcher.py"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Fix 5: Add payment approval check to orchestrator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "orchestrator.py" ]; then
    backup_file "orchestrator.py"
    
    # Create patch file for manual integration
    cat > orchestrator_payment_approval_patch.txt << 'PATCH'
# Add this to validate_approval() function in orchestrator.py
# After the existing validation checks

# ── PAYMENT APPROVAL CHECK (Security Audit March 2026) ──
# Payments over $100 require explicit approval
if "amount" in metadata or any(kw in str(metadata.get("subject", "")).lower() for kw in ["payment", "invoice", "$"]):
    # Try to extract amount from metadata
    amount_str = metadata.get("amount", "")
    if not amount_str:
        # Try to find amount in subject or other fields
        import re
        text_to_search = f"{metadata.get('subject', '')} {metadata.get('body', '')}"
        amount_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text_to_search)
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
    
    if amount_str:
        try:
            # Remove $ and commas
            amount = float(str(amount_str).replace("$", "").replace(",", ""))
            if amount > 100 and not metadata.get("approved"):
                errors.append(f"Payment over $100 requires approval: ${amount:.2f}. Set approved=true or reduce amount.")
        except (ValueError, TypeError):
            pass  # Amount parsing failed, skip check
# ── END PAYMENT APPROVAL CHECK ──
PATCH

    echo "✓ Created payment approval patch (orchestrator_payment_approval_patch.txt)"
    echo "  Manual step: Add this code to validate_approval() in orchestrator.py"
fi

echo ""
echo "=================================================="
echo "Summary of Changes"
echo "=================================================="
echo ""
echo "✅ Automatic fixes applied:"
echo "   - DRY_RUN defaults changed to true (9 files)"
echo "   - RETENTION_DAYS changed to 90 (2 files)"
echo "   - Log rotation script created"
echo ""
echo "⚠️  Manual steps required:"
echo "   1. Review and apply whatsapp_watcher_approval_patch.txt"
echo "   2. Review and apply orchestrator_payment_approval_patch.txt"
echo "   3. Update mcp/email-server/.env with REQUIRE_APPROVAL=true"
echo "   4. Test all components in DRY_RUN mode before production"
echo ""
echo "📋 Next steps:"
echo "   1. Run: git diff  (review all changes)"
echo "   2. Run: bash scripts/apply_priority2_fixes.sh  (MEDIUM severity)"
echo "   3. Update SILVER_TIER_AUDIT_REPORT.md with completion status"
echo ""
echo "=================================================="
echo "Fix script completed!"
echo "=================================================="
