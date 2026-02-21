#!/usr/bin/env bash
# task-claim-template.sh
# Atomically claim a task with collision detection

set -euo pipefail

TASK_ID="${1:?Usage: $0 <task-id>}"
AGENT_ID="${AGENT_ID:-agent-$(hostname)-$$}"
TASK_STORAGE_PATH="${TASK_STORAGE_PATH:-./tasks}"
TASK_LOCK_TIMEOUT="${TASK_LOCK_TIMEOUT:-300}"

# Audit logging
audit_log() {
    local level="$1"
    local action="$2"
    local task_id="$3"
    local status="$4"
    local message="${5:-}"

    echo "$(date -Iseconds) [$level] agent=$AGENT_ID action=$action task=$task_id status=$status $message" \
        >> "${TASK_AUDIT_LOG:-/dev/stderr}"
}

# Check if task exists and is claimable
check_task_claimable() {
    local task_id="$1"
    local task_file="$TASK_STORAGE_PATH/$task_id.json"

    if [[ ! -f "$task_file" ]]; then
        audit_log "ERROR" "CLAIM_CHECK" "$task_id" "NOT_FOUND"
        return 1
    fi

    # Parse current state and owner
    local current_state
    local current_owner
    current_state=$(jq -r '.state // "unknown"' "$task_file")
    current_owner=$(jq -r '.owner // ""' "$task_file")

    # Task is claimable if:
    # 1. State is "pending" and no owner
    # 2. State is "pending" and owner is stale (lock expired)
    if [[ "$current_state" != "pending" ]]; then
        audit_log "WARN" "CLAIM_CHECK" "$task_id" "NOT_CLAIMABLE" "state=$current_state"
        return 1
    fi

    if [[ -n "$current_owner" ]]; then
        # Check if lock is stale
        local claimed_at
        claimed_at=$(jq -r '.claimed_at // 0' "$task_file")
        local now
        now=$(date +%s)
        local elapsed=$((now - claimed_at))

        if [[ $elapsed -lt $TASK_LOCK_TIMEOUT ]]; then
            audit_log "WARN" "CLAIM_CHECK" "$task_id" "ALREADY_CLAIMED" "owner=$current_owner"
            return 1
        else
            audit_log "INFO" "CLAIM_CHECK" "$task_id" "STALE_LOCK" "owner=$current_owner elapsed=${elapsed}s"
        fi
    fi

    return 0
}

# Atomically claim task using rename operation
claim_task_atomic() {
    local task_id="$1"
    local task_file="$TASK_STORAGE_PATH/$task_id.json"
    local temp_file="$TASK_STORAGE_PATH/.$task_id.tmp.$$"
    local backup_file="$TASK_STORAGE_PATH/.$task_id.backup.$$"

    audit_log "INFO" "CLAIM_ATTEMPT" "$task_id" "STARTED"

    # Read current task data
    if ! cp "$task_file" "$backup_file"; then
        audit_log "ERROR" "CLAIM_ATTEMPT" "$task_id" "BACKUP_FAILED"
        return 1
    fi

    # Update task with claim information
    if ! jq --arg agent "$AGENT_ID" \
            --arg timestamp "$(date -Iseconds)" \
            --arg unix_time "$(date +%s)" \
            '.state = "in_progress" | .owner = $agent | .claimed_at = ($unix_time | tonumber) | .claimed_timestamp = $timestamp' \
            "$backup_file" > "$temp_file"; then
        audit_log "ERROR" "CLAIM_ATTEMPT" "$task_id" "UPDATE_FAILED"
        rm -f "$temp_file" "$backup_file"
        return 1
    fi

    # Atomic rename (this is the critical section)
    # If another agent renamed the file between our check and now, this will fail
    if mv "$temp_file" "$task_file" 2>/dev/null; then
        audit_log "INFO" "CLAIM_ATTEMPT" "$task_id" "SUCCESS"
        rm -f "$backup_file"
        return 0
    else
        audit_log "WARN" "CLAIM_ATTEMPT" "$task_id" "COLLISION" "Another agent claimed the task"
        rm -f "$temp_file" "$backup_file"
        return 1
    fi
}

# Main claim logic with retries
claim_task() {
    local task_id="$1"
    local retry_count="${TASK_CLAIM_RETRY_COUNT:-3}"
    local retry_delay="${TASK_CLAIM_RETRY_DELAY:-1}"

    for attempt in $(seq 1 "$retry_count"); do
        audit_log "INFO" "CLAIM" "$task_id" "ATTEMPT_$attempt"

        # Check if task is claimable
        if ! check_task_claimable "$task_id"; then
            audit_log "WARN" "CLAIM" "$task_id" "NOT_CLAIMABLE_ATTEMPT_$attempt"
            return 1
        fi

        # Attempt atomic claim
        if claim_task_atomic "$task_id"; then
            audit_log "INFO" "CLAIM" "$task_id" "SUCCESS_ATTEMPT_$attempt"
            echo "$task_id"
            return 0
        fi

        # Collision detected, wait and retry
        if [[ $attempt -lt $retry_count ]]; then
            audit_log "INFO" "CLAIM" "$task_id" "RETRY_WAIT" "delay=${retry_delay}s"
            sleep "$retry_delay"
        fi
    done

    audit_log "ERROR" "CLAIM" "$task_id" "FAILED_ALL_ATTEMPTS"
    return 1
}

# Execute claim
if claim_task "$TASK_ID"; then
    echo "Successfully claimed task: $TASK_ID"
    exit 0
else
    echo "Failed to claim task: $TASK_ID" >&2
    exit 1
fi
