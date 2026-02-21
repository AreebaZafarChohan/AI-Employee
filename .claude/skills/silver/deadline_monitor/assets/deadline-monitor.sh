#!/usr/bin/env bash
# deadline-monitor.sh
# Monitors task deadlines and sends notifications for upcoming or overdue tasks

set -euo pipefail

# Configuration
CHANNEL="${DEADLINE_MONITOR_CHANNEL:-slack}"
TASK_API="${TASK_MANAGEMENT_API_URL:-https://api.company.com/tasks}"
LOG_PATH="${NOTIFICATION_LOG_PATH:-/tmp/deadline_notifications.log}"
DEBUG="${DEADLINE_DEBUG_MODE:-false}"
TIMEZONE="${DEADLINE_TIMEZONE:-UTC}"
LEAD_TIME="${NOTIFICATION_LEAD_TIME:-24h}"
ESCALATION_DELAY="${ESCALATION_AFTER:-48h}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log_notification() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local user=$(whoami)
    
    echo "{\"timestamp\":\"${timestamp}\",\"level\":\"${level}\",\"user\":\"${user}\",\"message\":\"${message}\"}" >> "${LOG_PATH}"
}

# Convert ISO date to epoch for comparison
iso_to_epoch() {
    local iso_date="$1"
    # Remove timezone info and convert to epoch
    date -d "${iso_date%.*}" +%s 2>/dev/null || date -jf "%Y-%m-%dT%H:%M:%S" "${iso_date%.*}" +%s
}

# Fetch tasks with deadlines
fetch_deadline_tasks() {
    if [[ "$DEBUG" == "true" ]]; then
        echo "Debug: Fetching tasks from $TASK_API"
    fi
    
    # In a real implementation, this would call the API
    # curl -H "Authorization: Bearer $TOKEN" "$TASK_API?status=active"
    
    # Mock data for demonstration
    cat << 'EOF'
[
  {
    "id": "task1",
    "title": "Complete project proposal",
    "description": "Draft and submit the quarterly project proposal",
    "assignee": "alice.johnson",
    "deadline": "2026-02-08T10:00:00Z",
    "priority": "high",
    "tags": ["proposal", "critical"]
  },
  {
    "id": "task2",
    "title": "Code review",
    "description": "Review PR #1234 for the login feature",
    "assignee": "bob.smith",
    "deadline": "2026-02-06T15:00:00Z",
    "priority": "medium",
    "tags": ["review", "frontend"]
  },
  {
    "id": "task3",
    "title": "Client presentation",
    "description": "Prepare slides for client meeting",
    "assignee": "carol.davis",
    "deadline": "2026-02-05T09:00:00Z",
    "priority": "high",
    "tags": ["presentation", "client-facing"]
  }
]
EOF
}

# Send notification based on configured channel
send_notification() {
    local task_id="$1"
    local task_title="$2"
    local assignee="$3"
    local deadline="$4"
    local status="$5"  # upcoming, overdue, critical_overdue
    local message="$6"
    
    case "$CHANNEL" in
        "slack")
            # In a real implementation, this would send to Slack webhook
            # curl -X POST -H 'Content-Type: application/json' \
            #   -d "{\"text\":\"$message\"}" "$SLACK_WEBHOOK_URL"
            echo "📤 Slack: $message"
            ;;
        "email")
            # In a real implementation, this would send an email
            # mail -s "Task Deadline Alert" "$assignee@company.com" <<< "$message"
            echo "📧 Email: $message"
            ;;
        "teams")
            # In a real implementation, this would send to Teams webhook
            echo "💬 Teams: $message"
            ;;
        "webhook")
            # In a real implementation, this would send to custom webhook
            echo "🔗 Webhook: $message"
            ;;
        *)
            echo "❌ Unknown notification channel: $CHANNEL"
            return 1
            ;;
    esac
    
    log_notification "INFO" "Notification sent for task $task_id ($status): $message"
}

# Calculate time difference in hours
time_diff_hours() {
    local start="$1"
    local end="$2"
    local start_epoch=$(iso_to_epoch "$start")
    local end_epoch=$(iso_to_epoch "$end")
    echo $(( (end_epoch - start_epoch) / 3600 ))
}

# Process tasks and send notifications
process_tasks() {
    local tasks_json="$1"
    local current_time_iso=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local current_epoch=$(iso_to_epoch "$current_time_iso")
    
    local num_tasks=$(echo "$tasks_json" | jq 'length')
    
    for ((i=0; i<num_tasks; i++)); do
        local task=$(echo "$tasks_json" | jq ".[$i]")
        local task_id=$(echo "$task" | jq -r '.id')
        local task_title=$(echo "$task" | jq -r '.title')
        local assignee=$(echo "$task" | jq -r '.assignee')
        local deadline=$(echo "$task" | jq -r '.deadline')
        local priority=$(echo "$task" | jq -r '.priority')
        local tags=$(echo "$task" | jq -r '.tags | join(", ")')
        
        local deadline_epoch=$(iso_to_epoch "$deadline")
        local hours_until_deadline=$(( (deadline_epoch - current_epoch) / 3600 ))
        
        if [[ "$DEBUG" == "true" ]]; then
            echo "Debug: Task $task_id - Hours until deadline: $hours_until_deadline"
        fi
        
        # Determine notification type based on time until deadline
        if [[ $hours_until_deadline -lt 0 ]]; then
            # Task is overdue
            local overdue_hours=$(( -1 * hours_until_deadline ))
            local message="🚨 OVERDUE TASK ALERT 🚨\nTask: $task_title (ID: $task_id)\nAssignee: $assignee\nWas due: $deadline\nOverdue by: $overdue_hours hours\nPriority: $priority\nTags: $tags"
            
            if [[ $overdue_hours -ge 48 ]]; then
                # Critical overdue - escalate
                send_notification "$task_id" "$task_title" "$assignee" "$deadline" "critical_overdue" "$message"
            else
                # Regular overdue
                send_notification "$task_id" "$task_title" "$assignee" "$deadline" "overdue" "$message"
            fi
        elif [[ $hours_until_deadline -le 24 ]]; then
            # Task due within 24 hours
            local message="⏰ UPCOMING DEADLINE ⏰\nTask: $task_title (ID: $task_id)\nAssignee: $assignee\nDue: $deadline\nHours remaining: $hours_until_deadline\nPriority: $priority\nTags: $tags"
            send_notification "$task_id" "$task_title" "$assignee" "$deadline" "upcoming" "$message"
        fi
    done
}

# Main execution
main() {
    echo "👀 Starting deadline monitoring process..."
    echo "Channel: $CHANNEL"
    echo "Timezone: $TIMEZONE"
    
    # Fetch tasks with deadlines
    local tasks_data
    tasks_data=$(fetch_deadline_tasks)
    
    # Process tasks and send notifications
    process_tasks "$tasks_data"
    
    echo "✅ Deadline monitoring process completed!"
}

main "$@"