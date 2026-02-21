#!/usr/bin/env bash
# task-assigner.sh
# Automatically assigns tasks to team members based on workload and skills

set -euo pipefail

# Configuration
STRATEGY="${TASK_ASSIGNER_STRATEGY:-balanced}"
TEAM_API="${TEAM_MEMBERS_API_URL:-https://api.company.com/team}"
TASKS_API="${TASKS_API_URL:-https://api.company.com/tasks}"
LOG_PATH="${ASSIGNMENT_LOG_PATH:-/tmp/task_assignment.log}"
DEBUG="${TASK_ASSIGNER_DEBUG_MODE:-false}"
WORKLOAD_THRESHOLD="${TASK_ASSIGNER_WORKLOAD_THRESHOLD:-0.8}"
CACHE_TTL="${TASK_ASSIGNER_CACHE_TTL:-300}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log_assignment() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local user=$(whoami)
    
    echo "{\"timestamp\":\"${timestamp}\",\"level\":\"${level}\",\"user\":\"${user}\",\"message\":\"${message}\"}" >> "${LOG_PATH}"
}

# Fetch team member data
fetch_team_data() {
    if [[ "$DEBUG" == "true" ]]; then
        echo "Debug: Fetching team data from $TEAM_API"
    fi
    
    # In a real implementation, this would call the API
    # curl -H "Authorization: Bearer $TOKEN" "$TEAM_API"
    
    # Mock data for demonstration
    cat << 'EOF'
[
  {
    "id": "user1",
    "name": "Alice Johnson",
    "skills": ["javascript", "react", "nodejs"],
    "current_workload": 0.6,
    "availability": true,
    "preferred_hours": {"start": 9, "end": 17}
  },
  {
    "id": "user2", 
    "name": "Bob Smith",
    "skills": ["python", "django", "sql"],
    "current_workload": 0.4,
    "availability": true,
    "preferred_hours": {"start": 10, "end": 18}
  },
  {
    "id": "user3",
    "name": "Carol Davis",
    "skills": ["design", "ui", "ux"],
    "current_workload": 0.9,
    "availability": true,
    "preferred_hours": {"start": 8, "end": 16}
  }
]
EOF
}

# Fetch pending tasks
fetch_pending_tasks() {
    if [[ "$DEBUG" == "true" ]]; then
        echo "Debug: Fetching pending tasks from $TASKS_API"
    fi
    
    # In a real implementation, this would call the API
    # curl -H "Authorization: Bearer $TOKEN" "$TASKS_API?status=pending"
    
    # Mock data for demonstration
    cat << 'EOF'
[
  {
    "id": "task1",
    "title": "Fix login bug",
    "description": "Resolve authentication issue in login flow",
    "priority": "high",
    "required_skills": ["javascript", "react"],
    "estimated_hours": 2
  },
  {
    "id": "task2",
    "title": "Database optimization",
    "description": "Optimize slow queries in user table",
    "priority": "medium", 
    "required_skills": ["sql", "python"],
    "estimated_hours": 4
  }
]
EOF
}

# Calculate assignment score based on strategy
calculate_score() {
    local user_json="$1"
    local task_json="$2"
    local strategy="$3"
    
    # Extract data from JSON
    local user_workload=$(echo "$user_json" | jq -r '.current_workload')
    local user_skills=$(echo "$user_json" | jq -r '.skills | join(",")')
    local task_skills=$(echo "$task_json" | jq -r '.required_skills | join(",")')
    local task_priority=$(echo "$task_json" | jq -r '.priority')
    
    # Calculate skill match (simple percentage for demo)
    local skill_match=0
    IFS=',' read -ra REQ_SKILLS <<< "$task_skills"
    for skill in "${REQ_SKILLS[@]}"; do
        if [[ "$user_skills" == *"$skill"* ]]; then
            ((skill_match++))
        fi
    done
    local total_req_skills=${#REQ_SKILLS[@]}
    if [[ $total_req_skills -gt 0 ]]; then
        skill_match=$(echo "$skill_match $total_req_skills" | awk '{printf "%.2f", $1/$2}')
    else
        skill_match=0
    fi
    
    # Calculate workload factor (lower workload = higher score)
    local workload_factor=$(echo "1 - $user_workload" | bc -l)
    
    # Calculate priority factor
    local priority_factor=0.5  # Default
    if [[ "$task_priority" == "high" ]]; then
        priority_factor=1.0
    elif [[ "$task_priority" == "medium" ]]; then
        priority_factor=0.7
    fi
    
    # Calculate final score based on strategy
    case "$strategy" in
        "skill_priority")
            echo "$(echo "$skill_match" | bc -l)"
            ;;
        "workload_priority")
            echo "$(echo "$workload_factor" | bc -l)"
            ;;
        *)
            # Balanced strategy
            local skill_weight="${TASK_ASSIGNER_SKILL_WEIGHT:-0.6}"
            local workload_weight="${TASK_ASSIGNER_WORKLOAD_WEIGHT:-0.3}"
            local priority_weight="${TASK_ASSIGNER_PRIORITY_WEIGHT:-0.1}"
            
            local score=$(echo "$skill_match * $skill_weight + $workload_factor * $workload_weight + $priority_factor * $priority_weight" | bc -l)
            echo "$score"
            ;;
    esac
}

# Assign tasks to team members
assign_tasks() {
    local team_data="$1"
    local tasks_data="$2"
    
    # Parse tasks
    local num_tasks=$(echo "$tasks_data" | jq 'length')
    
    for ((i=0; i<num_tasks; i++)); do
        local task=$(echo "$tasks_data" | jq ".[$i]")
        local task_id=$(echo "$task" | jq -r '.id')
        local task_title=$(echo "$task" | jq -r '.title')
        
        if [[ "$DEBUG" == "true" ]]; then
            echo "Debug: Processing task $task_id: $task_title"
        fi
        
        # Find best candidate for this task
        local best_user=""
        local best_score=-1
        
        local num_users=$(echo "$team_data" | jq 'length')
        for ((j=0; j<num_users; j++)); do
            local user=$(echo "$team_data" | jq ".[$j]")
            local user_id=$(echo "$user" | jq -r '.id')
            local user_available=$(echo "$user" | jq -r '.availability')
            local user_workload=$(echo "$user" | jq -r '.current_workload')
            
            # Skip unavailable users or those exceeding workload threshold
            if [[ "$user_available" != "true" ]] || (( $(echo "$user_workload > $WORKLOAD_THRESHOLD" | bc -l) )); then
                continue
            fi
            
            local score=$(calculate_score "$user" "$task" "$STRATEGY")
            
            if (( $(echo "$score > $best_score" | bc -l) )); then
                best_score=$score
                best_user=$user_id
            fi
        done
        
        if [[ -n "$best_user" ]]; then
            # In a real implementation, this would assign the task via API
            # curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
            #   "$TASKS_API/$task_id/assign" -d "{\"assignee\": \"$best_user\"}"
            
            echo "✅ Assigned task '$task_title' (ID: $task_id) to user $best_user (Score: $best_score)"
            log_assignment "INFO" "Assigned task $task_id to user $best_user with score $best_score"
        else
            echo "⚠️  Could not find suitable assignee for task '$task_title' (ID: $task_id)"
            log_assignment "WARN" "Could not assign task $task_id - no suitable candidates found"
        fi
    done
}

# Main execution
main() {
    echo "🚀 Starting task assignment process..."
    echo "Strategy: $STRATEGY"
    
    # Fetch team and task data
    local team_data
    team_data=$(fetch_team_data)
    
    local tasks_data
    tasks_data=$(fetch_pending_tasks)
    
    # Perform assignments
    assign_tasks "$team_data" "$tasks_data"
    
    echo "✅ Task assignment process completed!"
}

main "$@"