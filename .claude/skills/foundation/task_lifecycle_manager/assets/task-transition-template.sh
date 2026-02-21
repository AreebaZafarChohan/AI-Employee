#!/usr/bin/env bash
# task-transition-template.sh
# Safely transition task state with validation

set -euo pipefail

TASK_ID="${1:?Usage: $0 <task-id> <new-state>}"
NEW_STATE="${2:?Usage: $0 <task-id> <new-state>}"
AGENT_ID="${AGENT_ID:-agent-$(hostname)-$$}"
TASK_STORAGE_PATH="${TASK_STORAGE_PATH:-./tasks}"

# Valid state transitions
declare -A VALID_TRANSITIONS=(
    ["pending:in_progress"]="1"
    ["in_progress:completed"]="1"
    ["in_progress:failed"]="1"
    ["in_progress:blocked"]="1"
    ["blocked:in_progress"]="1"
    ["failed:pending"]="1"        # Allow retry
)

audit_log() {
    local level="$1"
    local action="$2"
    local task_id="$3"
    local status="$4"
    local message="${5:-}"

    echo "$(date -Iseconds) [$level] agent=$AGENT_ID action=$action task=$task_id status=$status $message" \
        >> "${TASK_AUDIT_LOG:-/dev/stderr}"
}

# Validate state transition
validate_transition() {
    local current_state="$1"
    local new_state="$2"
    local transition_key="${current_state}:${new_state}"

    if [[ -n "${VALID_TRANSITIONS[$transition_key]:-}" ]]; then
        return 0
    else
        return 1
    fi
}

# Verify agent owns the task
verify_ownership() {
    local task_id="$1"
    local task_file="$TASK_STORAGE_PATH/$task_id.json"

    if [[ ! -f "$task_file" ]]; then
        audit_log "ERROR" "VERIFY_OWNERSHIP" "$task_id" "NOT_FOUND"
        return 1
    fi

    local current_owner
    current_owner=$(jq -r '.owner // ""' "$task_file")

    if [[ "$current_owner" != "$AGENT_ID" ]]; then
        audit_log "ERROR" "VERIFY_OWNERSHIP" "$task_id" "NOT_OWNER" "current_owner=$current_owner"
        return 1
    fi

    return 0
}

# Transition task state
transition_task() {
    local task_id="$1"
    local new_state="$2"
    local task_file="$TASK_STORAGE_PATH/$task_id.json"
    local temp_file="$TASK_STORAGE_PATH/.$task_id.tmp.$$"

    audit_log "INFO" "TRANSITION" "$task_id" "STARTED" "new_state=$new_state"

    # Verify ownership
    if ! verify_ownership "$task_id"; then
        return 1
    fi

    # Read current state
    local current_state
    current_state=$(jq -r '.state' "$task_file")

    # Validate transition
    if ! validate_transition "$current_state" "$new_state"; then
        audit_log "ERROR" "TRANSITION" "$task_id" "INVALID" "from=$current_state to=$new_state"
        echo "Invalid transition: $current_state -> $new_state" >&2
        return 1
    fi

    # Update state with metadata
    if ! jq --arg new_state "$new_state" \
            --arg timestamp "$(date -Iseconds)" \
            --arg agent "$AGENT_ID" \
            '.state = $new_state |
             .updated_at = $timestamp |
             .updated_by = $agent |
             .history += [{
                "from": .state,
                "to": $new_state,
                "timestamp": $timestamp,
                "agent": $agent
             }]' \
            "$task_file" > "$temp_file"; then
        audit_log "ERROR" "TRANSITION" "$task_id" "UPDATE_FAILED"
        rm -f "$temp_file"
        return 1
    fi

    # Atomic replace
    if mv "$temp_file" "$task_file"; then
        audit_log "INFO" "TRANSITION" "$task_id" "SUCCESS" "from=$current_state to=$new_state"

        # Special handling for terminal states
        if [[ "$new_state" == "completed" || "$new_state" == "failed" ]]; then
            # Clear owner on completion
            jq '.owner = null | .completed_at = (now | tostring)' "$task_file" > "$temp_file"
            mv "$temp_file" "$task_file"
            audit_log "INFO" "RELEASE" "$task_id" "AUTO_RELEASED"
        fi

        return 0
    else
        audit_log "ERROR" "TRANSITION" "$task_id" "ATOMIC_WRITE_FAILED"
        rm -f "$temp_file"
        return 1
    fi
}

# Execute transition
if transition_task "$TASK_ID" "$NEW_STATE"; then
    echo "Successfully transitioned task $TASK_ID to $NEW_STATE"
    exit 0
else
    echo "Failed to transition task $TASK_ID" >&2
    exit 1
fi
