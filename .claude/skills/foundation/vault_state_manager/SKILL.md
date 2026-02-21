# Vault State Manager Skill

## Overview

**Skill Name:** `vault_state_manager`
**Domain:** `foundation`
**Purpose:** Securely manage vault state operations including reading, writing, and updating sensitive configuration data without exposing secrets.

**Core Capabilities:**
- Secure vault state reading with environment-based authentication
- Atomic vault state writing with validation
- State merging and updating with conflict detection
- Audit logging of all vault operations
- Multi-user access control awareness
- Secret rotation support

**When to Use:**
- Reading application secrets from secure storage
- Updating configuration state in vault systems (HashiCorp Vault, AWS Secrets Manager, etc.)
- Implementing secret rotation workflows
- Auditing access to sensitive state
- Managing environment-specific configurations

**When NOT to Use:**
- Storing secrets in plain text files
- Managing non-sensitive configuration (use standard config files)
- Single-purpose secret reads (use direct API calls instead)
- Development-only mock secrets (use `.env.example` patterns)

---

## Impact Analysis

### Security Impact: **CRITICAL**
- **Secrets Exposure Risk:** High - misuse can leak credentials
- **Access Control:** Requires proper authentication and authorization
- **Audit Trail:** All operations must be logged for compliance
- **Encryption:** Data in transit and at rest must be encrypted

### System Impact: **HIGH**
- **Dependencies:** Vault client libraries, authentication providers
- **State Management:** Atomic operations required to prevent corruption
- **Failure Modes:** Network issues, authentication failures, permission errors
- **Recovery:** Rollback mechanisms needed for failed writes

### Operational Impact: **MEDIUM**
- **Monitoring:** Track read/write latency, error rates, auth failures
- **Alerting:** Failed authentication, unauthorized access attempts
- **Debugging:** Sanitized logs (never log actual secrets)
- **Performance:** Caching strategies for frequently accessed secrets

---

## Environment Variables

### Required Variables

```bash
# Primary vault authentication
VAULT_ADDR="https://vault.example.com"
VAULT_TOKEN="<token-from-secure-source>"  # Never hardcode
VAULT_NAMESPACE="<namespace>"             # Optional for Vault Enterprise

# Alternative: AWS Secrets Manager
AWS_REGION="us-east-1"
AWS_ACCESS_KEY_ID="<from-iam-role-preferred>"
AWS_SECRET_ACCESS_KEY="<from-iam-role-preferred>"

# Alternative: Azure Key Vault
AZURE_TENANT_ID="<tenant-id>"
AZURE_CLIENT_ID="<client-id>"
AZURE_CLIENT_SECRET="<from-managed-identity-preferred>"
AZURE_VAULT_NAME="<vault-name>"
```

### Optional Variables

```bash
# Operational configuration
VAULT_OPERATION_TIMEOUT="30s"
VAULT_MAX_RETRIES="3"
VAULT_AUDIT_LOG_PATH="./logs/vault-audit.log"
VAULT_CACHE_TTL="300"                     # 5 minutes default

# Development overrides (NEVER use in production)
VAULT_DEV_MODE="false"
VAULT_SKIP_VERIFY="false"                 # Only for dev with self-signed certs
```

---

## Network and Authentication Implications

### Network Requirements
1. **Egress Access:** Outbound HTTPS (443) to vault endpoints
2. **TLS/SSL:** Valid certificates required (exception: dev mode with explicit opt-in)
3. **Timeouts:** Configure appropriate timeouts for network instability
4. **Proxies:** Support HTTP_PROXY/HTTPS_PROXY environment variables

### Authentication Methods

#### Recommended: Managed Identity/IAM Roles
```bash
# AWS: Use IAM role attached to EC2/ECS/Lambda
# No credentials in environment - automatic AWS SDK resolution

# Azure: Use Managed Identity
# No credentials needed - Azure SDK auto-discovers identity

# GCP: Use Workload Identity
# No credentials needed - GCP SDK uses service account
```

#### Acceptable: Token-Based (with rotation)
```bash
# Vault token with limited TTL and renewable policy
VAULT_TOKEN="$(cat /run/secrets/vault-token)"  # From secret manager
# Implement token renewal before expiry
```

#### Not Recommended: Static Credentials
```bash
# Avoid static API keys/passwords in environment
# If unavoidable, rotate frequently and audit access
```

### Authorization Patterns
- **Principle of Least Privilege:** Request only necessary permissions
- **Path-Based Access:** Restrict to specific vault paths
- **Time-Based Tokens:** Use short-lived credentials with renewal
- **Audit All Access:** Log who accessed what and when

---

## Blueprints & Templates

### Template 1: Secure Vault Read Operation

**File:** `assets/vault-read-template.sh`

```bash
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
```

### Template 2: Secure Vault Write Operation

**File:** `assets/vault-write-template.sh`

```bash
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
```

### Template 3: Python Vault Manager Class

**File:** `assets/vault_manager.py`

```python
"""
vault_manager.py
Secure vault state management with proper error handling and auditing
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import hvac  # HashiCorp Vault client
from dataclasses import dataclass

# Configure logging (never log actual secrets)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VaultConfig:
    """Vault configuration from environment"""
    addr: str
    token: str
    namespace: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> 'VaultConfig':
        """Load configuration from environment variables"""
        addr = os.getenv('VAULT_ADDR')
        token = os.getenv('VAULT_TOKEN')

        if not addr or not token:
            raise ValueError("VAULT_ADDR and VAULT_TOKEN must be set")

        return cls(
            addr=addr,
            token=token,
            namespace=os.getenv('VAULT_NAMESPACE'),
            timeout=int(os.getenv('VAULT_OPERATION_TIMEOUT', '30')),
            max_retries=int(os.getenv('VAULT_MAX_RETRIES', '3'))
        )


class VaultStateManager:
    """Secure vault state manager with audit logging"""

    def __init__(self, config: Optional[VaultConfig] = None):
        self.config = config or VaultConfig.from_env()
        self.client = hvac.Client(
            url=self.config.addr,
            token=self.config.token,
            namespace=self.config.namespace
        )

        if not self.client.is_authenticated():
            raise RuntimeError("Vault authentication failed")

        logger.info("Vault client initialized", extra={
            'vault_addr': self.config.addr,
            'namespace': self.config.namespace
        })

    def _audit_log(self, action: str, path: str, status: str, error: Optional[str] = None):
        """Log audit trail for vault operations"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'path': path,
            'status': status,
            'user': os.getenv('USER', 'unknown')
        }

        if error:
            log_entry['error'] = error

        # Write to audit log file or send to logging system
        audit_log_path = os.getenv('VAULT_AUDIT_LOG_PATH')
        if audit_log_path:
            with open(audit_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        logger.info(f"Vault operation: {action} on {path} - {status}")

    def read_secret(self, path: str, mount_point: str = 'secret') -> Optional[Dict[str, Any]]:
        """
        Read secret from vault

        Args:
            path: Secret path (e.g., 'myapp/config')
            mount_point: Vault mount point (default: 'secret')

        Returns:
            Secret data dictionary or None if not found
        """
        full_path = f"{mount_point}/data/{path}"

        try:
            self._audit_log('READ', full_path, 'ATTEMPT')

            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point
            )

            self._audit_log('READ', full_path, 'SUCCESS')
            return response['data']['data']

        except hvac.exceptions.InvalidPath:
            self._audit_log('READ', full_path, 'NOT_FOUND')
            logger.warning(f"Secret not found at path: {full_path}")
            return None

        except hvac.exceptions.Forbidden:
            self._audit_log('READ', full_path, 'FORBIDDEN')
            logger.error(f"Access denied to path: {full_path}")
            raise

        except Exception as e:
            self._audit_log('READ', full_path, 'ERROR', str(e))
            logger.error(f"Error reading secret: {e}")
            raise

    def write_secret(self, path: str, data: Dict[str, Any], mount_point: str = 'secret') -> bool:
        """
        Write secret to vault

        Args:
            path: Secret path (e.g., 'myapp/config')
            data: Secret data dictionary
            mount_point: Vault mount point (default: 'secret')

        Returns:
            True if successful, False otherwise
        """
        full_path = f"{mount_point}/data/{path}"

        # Validate data
        if not data or not isinstance(data, dict):
            raise ValueError("Data must be a non-empty dictionary")

        try:
            self._audit_log('WRITE', full_path, 'ATTEMPT')

            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=mount_point
            )

            self._audit_log('WRITE', full_path, 'SUCCESS')
            return True

        except hvac.exceptions.Forbidden:
            self._audit_log('WRITE', full_path, 'FORBIDDEN')
            logger.error(f"Access denied to path: {full_path}")
            raise

        except Exception as e:
            self._audit_log('WRITE', full_path, 'ERROR', str(e))
            logger.error(f"Error writing secret: {e}")
            raise

    def update_secret(self, path: str, updates: Dict[str, Any], mount_point: str = 'secret') -> bool:
        """
        Update existing secret (merge with existing data)

        Args:
            path: Secret path
            updates: Dictionary of fields to update
            mount_point: Vault mount point

        Returns:
            True if successful
        """
        # Read existing data
        existing_data = self.read_secret(path, mount_point)

        if existing_data is None:
            logger.warning(f"Secret not found, creating new one at: {path}")
            return self.write_secret(path, updates, mount_point)

        # Merge updates
        merged_data = {**existing_data, **updates}

        return self.write_secret(path, merged_data, mount_point)

    def delete_secret(self, path: str, mount_point: str = 'secret') -> bool:
        """
        Delete secret from vault

        Args:
            path: Secret path
            mount_point: Vault mount point

        Returns:
            True if successful
        """
        full_path = f"{mount_point}/data/{path}"

        try:
            self._audit_log('DELETE', full_path, 'ATTEMPT')

            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=mount_point
            )

            self._audit_log('DELETE', full_path, 'SUCCESS')
            return True

        except Exception as e:
            self._audit_log('DELETE', full_path, 'ERROR', str(e))
            logger.error(f"Error deleting secret: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize manager (loads config from environment)
    manager = VaultStateManager()

    # Read secret
    config = manager.read_secret('myapp/config')
    if config:
        print(f"Retrieved {len(config)} configuration keys")

    # Update secret
    manager.update_secret('myapp/config', {
        'database_url': 'postgresql://...',
        'api_key': 'new-key-value'
    })

    print("Vault operations completed successfully")
```

---

## Validation Checklist

### Pre-Deployment Checklist

- [ ] **Environment Variables Verified**
  - [ ] All required variables are set
  - [ ] No hardcoded secrets in code
  - [ ] Credentials sourced from secure location (not shell history)
  - [ ] Development-only variables disabled in production

- [ ] **Authentication Tested**
  - [ ] Token/credentials are valid and not expired
  - [ ] Appropriate permissions granted (read/write as needed)
  - [ ] Token renewal mechanism in place (if applicable)
  - [ ] Fallback authentication tested

- [ ] **Network Access Confirmed**
  - [ ] Vault endpoint reachable from deployment environment
  - [ ] TLS/SSL certificates valid (no self-signed in production)
  - [ ] Proxy configuration applied if needed
  - [ ] Timeout values appropriate for network conditions

- [ ] **Audit Logging Configured**
  - [ ] Audit log path writable
  - [ ] Log rotation configured
  - [ ] Logs sanitized (no secret values)
  - [ ] Monitoring/alerting on audit logs enabled

- [ ] **Error Handling Implemented**
  - [ ] Network failures handled gracefully
  - [ ] Authentication failures logged and alerted
  - [ ] Permission errors reported clearly
  - [ ] Retry logic with exponential backoff

- [ ] **Security Review**
  - [ ] No secrets in logs or error messages
  - [ ] Principle of least privilege applied
  - [ ] Multi-user access patterns considered
  - [ ] Secret rotation strategy documented

### Post-Deployment Validation

- [ ] **Smoke Tests**
  - [ ] Read operation succeeds for known path
  - [ ] Write operation succeeds with valid data
  - [ ] Update operation merges correctly
  - [ ] Delete operation (if used) works properly

- [ ] **Monitoring**
  - [ ] Operation latency metrics collected
  - [ ] Error rate dashboard created
  - [ ] Authentication failure alerts configured
  - [ ] Audit log ingestion verified

- [ ] **Documentation**
  - [ ] Required environment variables documented
  - [ ] Example usage provided
  - [ ] Troubleshooting guide created
  - [ ] Runbook for common issues prepared

---

## Anti-Patterns

### ❌ Anti-Pattern 1: Hardcoding Secrets

**Bad Example:**
```python
# NEVER do this
VAULT_TOKEN = "s.abc123def456"
vault_client = hvac.Client(url="https://vault.example.com", token=VAULT_TOKEN)
```

**Why It's Bad:**
- Secrets committed to version control
- Visible in code reviews and logs
- Difficult to rotate
- Security audit nightmare

**Correct Approach:**
```python
import os

vault_token = os.getenv('VAULT_TOKEN')
if not vault_token:
    raise ValueError("VAULT_TOKEN environment variable must be set")

vault_client = hvac.Client(
    url=os.getenv('VAULT_ADDR'),
    token=vault_token
)
```

---

### ❌ Anti-Pattern 2: Assuming Single-User Access

**Bad Example:**
```python
# Assuming you're the only user
def write_config(data):
    # No conflict detection
    vault.write('app/config', data)
```

**Why It's Bad:**
- Race conditions in multi-user environments
- Last write wins (data loss)
- No audit trail of who changed what

**Correct Approach:**
```python
def write_config(data, user_id):
    # Read current version
    current = vault.read('app/config')

    if current and current.get('version') != data.get('expected_version'):
        logger.warning(f"Conflict detected - current version mismatch")
        raise ConflictError("Configuration changed since last read")

    # Include metadata
    data['last_modified_by'] = user_id
    data['last_modified_at'] = datetime.utcnow().isoformat()
    data['version'] = (current.get('version', 0) + 1) if current else 1

    vault.write('app/config', data)
    audit_log('WRITE', 'app/config', user_id, 'SUCCESS')
```

---

### ❌ Anti-Pattern 3: Storing Secrets in Plain Files

**Bad Example:**
```bash
# Writing secrets to disk
vault read secret/myapp/config > config.json
cat config.json  # Contains plaintext secrets
```

**Why It's Bad:**
- Secrets persisted on disk (forensics risk)
- File permissions often overlooked
- Easy to accidentally commit
- Violates least privilege principle

**Correct Approach:**
```bash
# Use process substitution or environment variables
export DB_PASSWORD=$(vault kv get -field=password secret/myapp/db)

# Or pipe directly to consuming process
vault kv get -format=json secret/myapp/config | jq -r '.data.data' | myapp --config-stdin

# Never write secrets to files unless encrypted and necessary
```

---

### ❌ Anti-Pattern 4: Ignoring Token Expiration

**Bad Example:**
```python
# Token expires but no renewal
vault_client = hvac.Client(url=vault_url, token=vault_token)

# Hours later...
vault_client.read('secret/data')  # Fails with auth error
```

**Why It's Bad:**
- Service interruption when token expires
- No graceful degradation
- Manual intervention required

**Correct Approach:**
```python
import hvac
from datetime import datetime, timedelta

class VaultClientWithRenewal:
    def __init__(self, url, token):
        self.client = hvac.Client(url=url, token=token)
        self.token_ttl = None
        self.last_renewal = None

    def ensure_authenticated(self):
        # Check token validity
        if not self.client.is_authenticated():
            raise RuntimeError("Vault token invalid")

        # Renew if approaching expiration
        lookup = self.client.lookup_token()
        ttl = lookup['data']['ttl']

        if ttl < 600:  # Less than 10 minutes
            logger.info("Renewing vault token")
            self.client.renew_token()
            self.last_renewal = datetime.utcnow()

    def read(self, path):
        self.ensure_authenticated()
        return self.client.read(path)
```

---

### ❌ Anti-Pattern 5: Logging Secret Values

**Bad Example:**
```python
# NEVER log actual secret values
secret = vault.read('secret/api-key')
logger.info(f"Retrieved API key: {secret['data']['key']}")
```

**Why It's Bad:**
- Secrets in log files (often retained long-term)
- Log aggregation systems expose secrets
- Compliance violations
- Security team nightmares

**Correct Approach:**
```python
secret = vault.read('secret/api-key')
# Log that operation succeeded, not the content
logger.info(
    "Retrieved API key",
    extra={
        'path': 'secret/api-key',
        'key_count': len(secret['data']),
        'has_key': 'key' in secret['data']
        # Never log the actual key value
    }
)
```

---

## Related Documentation

- [patterns.md](./docs/patterns.md) - Common vault integration patterns
- [impact-checklist.md](./docs/impact-checklist.md) - Full security impact assessment
- [gotchas.md](./docs/gotchas.md) - Common pitfalls and troubleshooting

---

## Support and Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify `VAULT_TOKEN` is current and not expired
   - Check token has required policies attached
   - Confirm namespace is correct (for Vault Enterprise)

2. **Network Timeouts**
   - Increase `VAULT_OPERATION_TIMEOUT`
   - Check network connectivity to vault endpoint
   - Verify firewall rules allow egress to port 443

3. **Permission Denied**
   - Review vault policies for the token
   - Ensure path matches policy rules exactly
   - Check if namespace is required

4. **Secrets Not Found**
   - Verify secret path is correct (KV v2 uses `data` in path)
   - Confirm mount point matches vault configuration
   - Check if secret was deleted or never created

### Getting Help

- Review audit logs for detailed error information
- Use `vault token lookup` to verify token capabilities
- Consult vault server logs for server-side errors
- Escalate to security team for permission issues

---

**Version:** 1.0.0
**Last Updated:** 2026-02-06
**Maintainer:** Foundation Team
