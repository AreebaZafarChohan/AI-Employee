#!/usr/bin/env bash
# Test Daily Briefing Script
# Simulates scheduled run for testing
#
# Usage:
#   ./test_daily_briefing.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "Testing Daily Briefing Script"
echo "========================================"
echo

# Check if script exists
if [[ ! -f "$SCRIPT_DIR/daily_briefing.sh" ]]; then
    echo "ERROR: daily_briefing.sh not found in $SCRIPT_DIR"
    exit 1
fi

echo "1. Checking script permissions..."
if [[ -x "$SCRIPT_DIR/daily_briefing.sh" ]]; then
    echo "   ✓ Script is executable"
else
    echo "   ⚠ Script is not executable - fixing..."
    chmod +x "$SCRIPT_DIR/daily_briefing.sh"
    echo "   ✓ Made executable"
fi

echo
echo "2. Running daily briefing script..."
echo "----------------------------------------"

# Run the script
"$SCRIPT_DIR/daily_briefing.sh"

EXIT_CODE=$?

echo "----------------------------------------"
echo
echo "3. Test Results:"
echo "   Exit code: $EXIT_CODE"

if [[ $EXIT_CODE -eq 0 ]]; then
    echo "   ✓ Test PASSED"
else
    echo "   ✗ Test FAILED"
fi

echo
echo "4. Checking log file..."
LOG_FILE=$(ls -t "$SCRIPT_DIR/../AI-Employee-Vault/Logs/daily-briefing-"*.log 2>/dev/null | head -1)

if [[ -n "$LOG_FILE" ]]; then
    echo "   ✓ Log file found: $LOG_FILE"
    echo
    echo "   Last 10 lines:"
    echo "   ---"
    tail -10 "$LOG_FILE" | sed 's/^/   /'
    echo "   ---"
else
    echo "   ⚠ No log file found"
fi

echo
echo "========================================"
echo "Test Complete"
echo "========================================"

exit $EXIT_CODE
