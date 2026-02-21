#!/usr/bin/env bash
# company-policy-validator.sh
# Validates documents against company handbook policies

set -euo pipefail

# Configuration
RULES_PATH="${HANDBOOK_RULES_PATH:-/etc/handbook/rules.json}"
AUDIT_LOG="${AUDIT_LOG_PATH:-/tmp/handbook-audit.log}"
DEBUG="${HANDBOOK_DEBUG_MODE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log_event() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local user=$(whoami)
    
    echo "{\"timestamp\":\"${timestamp}\",\"level\":\"${level}\",\"user\":\"${user}\",\"message\":\"${message}\"}" >> "${AUDIT_LOG}"
}

# Validate input file
validate_document() {
    local file_path="$1"
    local violations=()
    
    if [[ ! -f "$file_path" ]]; then
        echo -e "${RED}Error: File does not exist: ${file_path}${NC}" >&2
        return 1
    fi
    
    # Check file size
    local max_size=${HANDBOOK_MAX_FILE_SIZE:-10485760}
    local file_size=$(stat -c%s "$file_path")
    if [[ $file_size -gt $max_size ]]; then
        violations+=("File exceeds maximum size limit of $(($max_size / 1024))KB")
    fi
    
    # Read file content
    local content
    content=$(cat "$file_path")
    
    # Load rules
    if [[ ! -f "$RULES_PATH" ]]; then
        echo -e "${RED}Error: Rules file not found: ${RULES_PATH}${NC}" >&2
        return 1
    fi
    
    # Check for prohibited patterns (simplified example)
    # In a real implementation, this would use jq to parse rules.json
    if echo "$content" | grep -qiE "(password|secret|token|api_key|private_key)"; then
        violations+=("Potential sensitive information detected")
    fi
    
    if echo "$content" | grep -qiE "(confidential|proprietary|internal use only)"; then
        violations+=("Confidential marking detected without proper authorization")
    fi
    
    # Log validation event
    if [[ ${#violations[@]} -eq 0 ]]; then
        log_event "INFO" "Document validated successfully: $file_path"
        echo -e "${GREEN}✓ Document complies with company policies${NC}"
        return 0
    else
        log_event "WARN" "Policy violations found in $file_path: ${violations[*]}"
        echo -e "${RED}✗ Policy violations detected:${NC}"
        for violation in "${violations[@]}"; do
            echo -e "  - $violation"
        done
        return 1
    fi
}

# Main execution
main() {
    if [[ $# -ne 1 ]]; then
        echo "Usage: $0 <document_path>"
        exit 1
    fi
    
    local doc_path="$1"
    
    if [[ "$DEBUG" == "true" ]]; then
        echo "Debug: Validating document: $doc_path"
        echo "Debug: Using rules from: $RULES_PATH"
    fi
    
    validate_document "$doc_path"
    local result=$?
    
    exit $result
}

main "$@"