#!/bin/bash
# Query audit logs by various criteria

VAULT_PATH="${VAULT_PATH:-/vault}"
LOGS_DIR="${LOGS_DIR:-${VAULT_PATH}/Logs}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Usage
function usage() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  --date DATE           Filter by date (YYYY-MM-DD)"
  echo "  --start-date DATE     Start date for range query"
  echo "  --end-date DATE       End date for range query"
  echo "  --actor NAME          Filter by actor name"
  echo "  --action TYPE         Filter by action type"
  echo "  --status STATUS       Filter by result status (success|failure|error)"
  echo "  --resource-id ID      Filter by resource ID"
  echo "  --count               Count entries (instead of displaying)"
  echo "  --summary             Show summary statistics"
  echo ""
  echo "Examples:"
  echo "  $0 --date 2025-01-15 --actor lex"
  echo "  $0 --start-date 2025-01-01 --end-date 2025-01-15 --status failure"
  echo "  $0 --date 2025-01-15 --summary"
  exit 1
}

# Parse arguments
DATE=""
START_DATE=""
END_DATE=""
ACTOR=""
ACTION=""
STATUS=""
RESOURCE_ID=""
COUNT_ONLY=false
SUMMARY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --date)
      DATE="$2"
      shift 2
      ;;
    --start-date)
      START_DATE="$2"
      shift 2
      ;;
    --end-date)
      END_DATE="$2"
      shift 2
      ;;
    --actor)
      ACTOR="$2"
      shift 2
      ;;
    --action)
      ACTION="$2"
      shift 2
      ;;
    --status)
      STATUS="$2"
      shift 2
      ;;
    --resource-id)
      RESOURCE_ID="$2"
      shift 2
      ;;
    --count)
      COUNT_ONLY=true
      shift
      ;;
    --summary)
      SUMMARY=true
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

# Determine log files to search
if [ -n "$DATE" ]; then
  LOG_FILES="${LOGS_DIR}/${DATE}.json"
elif [ -n "$START_DATE" ] && [ -n "$END_DATE" ]; then
  LOG_FILES=$(find "$LOGS_DIR" -name "*.json" -newermt "$START_DATE" ! -newermt "$END_DATE" | sort)
else
  # Default: today's log
  DATE=$(date -u +%Y-%m-%d)
  LOG_FILES="${LOGS_DIR}/${DATE}.json"
fi

# Build jq filter
JQ_FILTER="."

if [ -n "$ACTOR" ]; then
  JQ_FILTER="$JQ_FILTER | select(.actor.name == \"$ACTOR\")"
fi

if [ -n "$ACTION" ]; then
  JQ_FILTER="$JQ_FILTER | select(.action.type == \"$ACTION\")"
fi

if [ -n "$STATUS" ]; then
  JQ_FILTER="$JQ_FILTER | select(.result.status == \"$STATUS\")"
fi

if [ -n "$RESOURCE_ID" ]; then
  JQ_FILTER="$JQ_FILTER | select(.resource.id == \"$RESOURCE_ID\")"
fi

# Execute query
RESULTS=$(cat $LOG_FILES 2>/dev/null | jq -c "$JQ_FILTER" 2>/dev/null)

if [ -z "$RESULTS" ]; then
  echo -e "${YELLOW}No log entries found${NC}"
  exit 0
fi

# Display results
if [ "$COUNT_ONLY" = true ]; then
  COUNT=$(echo "$RESULTS" | wc -l)
  echo "$COUNT"
elif [ "$SUMMARY" = true ]; then
  echo -e "${GREEN}=== Log Summary ===${NC}"
  echo ""

  # Total count
  TOTAL=$(echo "$RESULTS" | wc -l)
  echo "Total entries: $TOTAL"
  echo ""

  # By actor
  echo "By Actor:"
  echo "$RESULTS" | jq -r '.actor.name' | sort | uniq -c | sort -rn | while read count actor; do
    echo "  $actor: $count"
  done
  echo ""

  # By action
  echo "By Action:"
  echo "$RESULTS" | jq -r '.action.type' | sort | uniq -c | sort -rn | while read count action; do
    echo "  $action: $count"
  done
  echo ""

  # By status
  echo "By Status:"
  echo "$RESULTS" | jq -r '.result.status' | sort | uniq -c | sort -rn | while read count status; do
    if [ "$status" = "success" ]; then
      echo -e "  ${GREEN}$status: $count${NC}"
    elif [ "$status" = "failure" ] || [ "$status" = "error" ]; then
      echo -e "  ${RED}$status: $count${NC}"
    else
      echo "  $status: $count"
    fi
  done

else
  # Display formatted entries
  echo "$RESULTS" | jq -r '. | "\(.timestamp) [\(.actor.name)] \(.action.type) \(.resource.id) → \(.result.status)"' | while read line; do
    if echo "$line" | grep -q "success"; then
      echo -e "${GREEN}$line${NC}"
    elif echo "$line" | grep -qE "(failure|error)"; then
      echo -e "${RED}$line${NC}"
    else
      echo "$line"
    fi
  done
fi
