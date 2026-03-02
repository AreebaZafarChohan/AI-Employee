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
echo "Root: $ROOT"
echo ""

# Rotate root logs
if [ -d "$LOGS_DIR" ]; then
    COUNT=$(find "$LOGS_DIR" -name "*.log" -type f -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)
    if [ "$COUNT" -gt 0 ]; then
        find "$LOGS_DIR" -name "*.log" -type f -mtime +$RETENTION_DAYS -delete
        echo "✓ Deleted $COUNT old log files from: $LOGS_DIR"
    else
        echo "✓ No old logs to delete in: $LOGS_DIR"
    fi
else
    echo "⊘ Directory not found: $LOGS_DIR"
fi

# Rotate vault logs
if [ -d "$VAULT_LOGS" ]; then
    COUNT=$(find "$VAULT_LOGS" -name "*.json" -type f -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)
    if [ "$COUNT" -gt 0 ]; then
        find "$VAULT_LOGS" -name "*.json" -type f -mtime +$RETENTION_DAYS -delete
        echo "✓ Deleted $COUNT old log files from: $VAULT_LOGS"
    else
        echo "✓ No old logs to delete in: $VAULT_LOGS"
    fi
else
    echo "⊘ Directory not found: $VAULT_LOGS"
fi

# Rotate MCP server logs
for mcp_dir in "$ROOT"/mcp/*/logs; do
    if [ -d "$mcp_dir" ]; then
        COUNT=$(find "$mcp_dir" -name "*.json" -type f -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)
        if [ "$COUNT" -gt 0 ]; then
            find "$mcp_dir" -name "*.json" -type f -mtime +$RETENTION_DAYS -delete
            echo "✓ Deleted $COUNT old log files from: $mcp_dir"
        else
            echo "✓ No old logs to delete in: $mcp_dir"
        fi
    fi
done

echo ""
echo "Log rotation complete!"
echo "Finished at: $(date)"
