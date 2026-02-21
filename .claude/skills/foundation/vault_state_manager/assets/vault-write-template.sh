#!/usr/bin/env bash
# vault-write-template.sh
# Securely write/update secrets in vault with validation

set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:?VAULT_ADDR must be set}"
VAULT_TOKEN="${VAULT_TOKEN:?VAULT_TOKEN must be set}"
SECRET_PATH="${1:?Usage: $0 <secret-path> <json-data>}"
SECRET_DATA="${2:?Usage: $0 <secret-path> <json-data>}"

audit_log() {
    local action="$1"
    local path="$2"
    local status="$3"
    echo "$(date -Iseconds) | action=$action path=$path status=$status user=$(whoami)" \
        >> "${VAULT_AUDIT_LOG_PATH:-/dev/stderr}"
}

# Validate JSON data
validate_json() {
    if ! echo "$1" | jq empty 2>/dev/null; then
        echo "Invalid JSON data provided" >&2
        return 1
    fi

    # Check for common mistakes
    if echo "$1" | grep -qE '(password|secret|key).*=.*\$\{'; then
        echo "Warning: Detected potential template variable in secret data" >&2
        return 1
    fi

    return 0
}

# Write secret to vault
write_secret() {
    local path="$1"
    local data="$2"

    # Validate before writing
    if ! validate_json "$data"; then
        audit_log "WRITE_ATTEMPT" "$path" "VALIDATION_FAILED"
        return 1
    fi

    audit_log "WRITE_ATTEMPT" "$path" "STARTED"

    local response
    if response=$(curl -sSf -X POST \
        -H "X-Vault-Token: $VAULT_TOKEN" \
        -H "X-Vault-Namespace: ${VAULT_NAMESPACE:-}" \
        -H "Content-Type: application/json" \
        -d "$data" \
        "${VAULT_ADDR}/v1/${path}" 2>&1); then

        audit_log "WRITE_ATTEMPT" "$path" "SUCCESS"
        echo "$response"
        return 0
    else
        audit_log "WRITE_ATTEMPT" "$path" "FAILED"
        echo "Error writing secret: $response" >&2
        return 1
    fi
}

# Main execution
if ! write_secret "$SECRET_PATH" "$SECRET_DATA"; then
    echo "Failed to write secret to path: $SECRET_PATH" >&2
    exit 1
fi

# Usage: ./vault-write-template.sh secret/data/myapp/config '{"data":{"key":"value"}}'
