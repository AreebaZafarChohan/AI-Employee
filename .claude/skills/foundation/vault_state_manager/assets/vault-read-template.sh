#!/usr/bin/env bash
# vault-read-template.sh
# Securely read secrets from vault without exposing values

set -euo pipefail

# Configuration (from environment)
VAULT_ADDR="${VAULT_ADDR:?VAULT_ADDR must be set}"
VAULT_TOKEN="${VAULT_TOKEN:?VAULT_TOKEN must be set}"
SECRET_PATH="${1:?Usage: $0 <secret-path>}"

# Audit logging function
audit_log() {
    local action="$1"
    local path="$2"
    local status="$3"
    echo "$(date -Iseconds) | action=$action path=$path status=$status user=$(whoami)" \
        >> "${VAULT_AUDIT_LOG_PATH:-/dev/stderr}"
}

# Read secret from vault
read_secret() {
    local path="$1"
    local response

    audit_log "READ_ATTEMPT" "$path" "STARTED"

    if response=$(curl -sSf \
        -H "X-Vault-Token: $VAULT_TOKEN" \
        -H "X-Vault-Namespace: ${VAULT_NAMESPACE:-}" \
        "${VAULT_ADDR}/v1/${path}" 2>&1); then

        audit_log "READ_ATTEMPT" "$path" "SUCCESS"
        echo "$response"
        return 0
    else
        audit_log "READ_ATTEMPT" "$path" "FAILED"
        echo "Error reading secret: $response" >&2
        return 1
    fi
}

# Main execution
if ! read_secret "$SECRET_PATH"; then
    echo "Failed to read secret from path: $SECRET_PATH" >&2
    exit 1
fi

# Usage: ./vault-read-template.sh secret/data/myapp/config
# Output: JSON response (parse with jq in calling script)
