# Vault State Manager - Common Gotchas & Troubleshooting

## Overview
This document catalogs common mistakes, edge cases, and troubleshooting guidance for vault state management operations.

---

## 1. Authentication Issues

### Gotcha: Token Expired Silently

**Symptom:**
```
Error: permission denied
```

**Problem:**
Vault tokens have a TTL, and when they expire, operations fail with generic "permission denied" errors rather than "token expired".

**Solution:**
```python
# Always check token validity before operations
vault_client = hvac.Client(url=vault_url, token=vault_token)

if not vault_client.is_authenticated():
    raise RuntimeError("Vault token is invalid or expired")

# Check remaining TTL
token_info = vault_client.lookup_token()
ttl_seconds = token_info['data']['ttl']

if ttl_seconds < 600:  # Less than 10 minutes
    print(f"Warning: Token expires in {ttl_seconds} seconds")
    # Renew token if possible
    vault_client.renew_token()
```

**Prevention:**
- Implement automatic token renewal
- Monitor token TTL in logs
- Set up alerts for tokens nearing expiration
- Use renewable tokens with appropriate policies

---

### Gotcha: Wrong Namespace for Vault Enterprise

**Symptom:**
```
Error: namespace not found
```

**Problem:**
Vault Enterprise uses namespaces, but the client isn't configured with the correct namespace.

**Solution:**
```bash
# Set namespace in environment
export VAULT_NAMESPACE="my-team"

# Or in code
vault_client = hvac.Client(
    url=vault_url,
    token=vault_token,
    namespace="my-team"
)
```

**Prevention:**
- Always specify namespace explicitly for Vault Enterprise
- Document required namespace in configuration
- Validate namespace exists before operations

---

### Gotcha: Insufficient Policy Permissions

**Symptom:**
```
Error: permission denied on path 'secret/data/myapp/config'
```

**Problem:**
Token's attached policies don't grant access to the requested path.

**Diagnosis:**
```bash
# Check current token's policies
vault token lookup

# View policy contents
vault policy read my-policy

# Test specific capability
vault token capabilities secret/data/myapp/config
```

**Solution:**
```hcl
# Update policy to grant required access
path "secret/data/myapp/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/myapp/*" {
  capabilities = ["list"]
}
```

**Prevention:**
- Follow principle of least privilege
- Test policies in dev before production
- Document required permissions clearly
- Use policy templates for consistency

---

## 2. Path and Naming Issues

### Gotcha: KV v2 Path Confusion

**Symptom:**
```
Error: invalid path
```

**Problem:**
KV secrets engine version 2 requires `data` and `metadata` in paths, but version 1 doesn't.

**Wrong:**
```python
# KV v2 mounted at 'secret/'
vault.read('secret/myapp/config')  # ❌ Missing 'data'
```

**Correct:**
```python
# KV v2 path structure
vault.read('secret/data/myapp/config')  # ✅ Correct

# Or use the KV v2 specific method
vault.secrets.kv.v2.read_secret_version(
    path='myapp/config',
    mount_point='secret'
)
```

**Detection:**
```bash
# Check KV version
vault secrets list -detailed

# Look for 'version' field
# version 1: kv
# version 2: kv-v2
```

**Prevention:**
- Always check KV version during setup
- Use version-specific client methods
- Document KV version in configuration

---

### Gotcha: Trailing Slashes in Paths

**Symptom:**
Secret writes succeed but reads fail, or vice versa.

**Problem:**
```python
# Inconsistent path usage
vault.write('secret/data/myapp/config/')  # Trailing slash
vault.read('secret/data/myapp/config')    # No trailing slash

# These are treated as different paths!
```

**Solution:**
```python
# Normalize paths consistently
def normalize_path(path: str) -> str:
    """Remove trailing slashes from paths"""
    return path.rstrip('/')

# Use normalized paths everywhere
vault.read(normalize_path(secret_path))
vault.write(normalize_path(secret_path), data)
```

**Prevention:**
- Establish path naming convention
- Use helper functions for path construction
- Add validation in wrapper classes

---

## 3. Data Format Issues

### Gotcha: KV v2 Requires Nested Data Structure

**Symptom:**
```
Error: invalid data format
```

**Problem:**
KV v2 requires secrets wrapped in a `data` key.

**Wrong:**
```python
# Direct data for KV v2
vault.write('secret/data/myapp/config', {
    'api_key': 'abc123',
    'db_password': 'secret'
})  # ❌ Missing 'data' wrapper
```

**Correct:**
```python
# Properly wrapped for KV v2
vault.write('secret/data/myapp/config', {
    'data': {
        'api_key': 'abc123',
        'db_password': 'secret'
    }
})  # ✅ Correct structure

# Or use the KV v2 specific method (handles wrapping automatically)
vault.secrets.kv.v2.create_or_update_secret(
    path='myapp/config',
    secret={'api_key': 'abc123', 'db_password': 'secret'},
    mount_point='secret'
)
```

**Prevention:**
- Use KV version-specific client methods
- Create wrapper functions that handle formatting
- Add schema validation before writes

---

### Gotcha: Reading Non-Existent Secrets

**Symptom:**
Application crashes with `NoneType` errors.

**Problem:**
```python
# Assumes secret exists
config = vault.read('secret/data/myapp/config')
db_password = config['data']['data']['db_password']  # ❌ Crashes if secret doesn't exist
```

**Correct:**
```python
# Defensive reading with defaults
config = vault.read('secret/data/myapp/config')

if config is None:
    print("Secret not found, using defaults")
    db_password = os.getenv('DB_PASSWORD', 'default-for-dev')
else:
    db_password = config['data']['data'].get('db_password')

if not db_password:
    raise ValueError("Database password not configured")
```

**Prevention:**
- Always check for `None` returns
- Provide sensible defaults for development
- Fail fast on critical missing secrets in production
- Use schema validation

---

## 4. Network and Connectivity Issues

### Gotcha: Certificate Verification Failures

**Symptom:**
```
Error: certificate verify failed: self signed certificate
```

**Problem:**
Vault server using self-signed certificate, and client enforces verification.

**Wrong Solution:**
```python
# NEVER do this in production
import urllib3
urllib3.disable_warnings()
vault_client = hvac.Client(url=vault_url, token=token, verify=False)
```

**Correct Solutions:**

**Option 1: Add CA certificate (Recommended)**
```python
vault_client = hvac.Client(
    url=vault_url,
    token=token,
    verify='/path/to/ca-cert.pem'
)
```

**Option 2: Development-only override**
```python
# Only for development environments
if os.getenv('VAULT_DEV_MODE') == 'true':
    vault_client = hvac.Client(url=vault_url, token=token, verify=False)
else:
    vault_client = hvac.Client(url=vault_url, token=token)
```

**Prevention:**
- Use proper CA-signed certificates in production
- Document certificate setup requirements
- Never disable verification in production
- Use separate dev vault instances

---

### Gotcha: Timeout Too Short for Slow Networks

**Symptom:**
Intermittent timeout errors on vault operations.

**Problem:**
```python
# Default timeout might be too short
vault_client = hvac.Client(url=vault_url, token=token)
# Default timeout varies by client, often 30s
```

**Solution:**
```python
# Configure appropriate timeout
import os

timeout_seconds = int(os.getenv('VAULT_OPERATION_TIMEOUT', '60'))

vault_client = hvac.Client(
    url=vault_url,
    token=token,
    timeout=timeout_seconds
)
```

**Prevention:**
- Tune timeout based on network conditions
- Implement retry logic with exponential backoff
- Monitor operation latency
- Set different timeouts for read vs. write operations

---

### Gotcha: Proxy Configuration Not Applied

**Symptom:**
Cannot reach vault endpoint despite correct URL.

**Problem:**
Corporate proxy not configured, or environment variables not propagated.

**Solution:**
```bash
# Set proxy environment variables
export HTTP_PROXY="http://proxy.corp.com:8080"
export HTTPS_PROXY="http://proxy.corp.com:8080"
export NO_PROXY="localhost,127.0.0.1,.corp.com"

# Or in code
import os
import hvac

vault_client = hvac.Client(
    url=vault_url,
    token=token,
    proxies={
        'http': os.getenv('HTTP_PROXY'),
        'https': os.getenv('HTTPS_PROXY')
    }
)
```

**Prevention:**
- Document proxy requirements
- Test from actual deployment environment
- Check proxy authentication if required
- Validate NO_PROXY exclusions

---

## 5. Concurrency and Race Conditions

### Gotcha: Lost Updates in Multi-User Scenarios

**Symptom:**
Configuration changes disappear or get overwritten.

**Problem:**
```python
# Two processes updating same secret simultaneously
# Process A
config_a = vault.read('secret/data/app/config')
config_a['data']['data']['setting'] = 'value_a'
vault.write('secret/data/app/config', config_a['data'])

# Process B (running concurrently)
config_b = vault.read('secret/data/app/config')
config_b['data']['data']['another_setting'] = 'value_b'
vault.write('secret/data/app/config', config_b['data'])

# Result: Process A's changes are lost!
```

**Solution:**
```python
def update_secret_with_retry(path, updates, max_retries=3):
    """Update secret with optimistic locking"""
    for attempt in range(max_retries):
        # Read current version
        current = vault.secrets.kv.v2.read_secret_version(
            path=path.replace('secret/data/', ''),
            mount_point='secret'
        )

        current_version = current['data']['metadata']['version']
        current_data = current['data']['data']

        # Merge updates
        merged = {**current_data, **updates}

        try:
            # Write with CAS (Check-And-Set)
            vault.secrets.kv.v2.create_or_update_secret(
                path=path.replace('secret/data/', ''),
                secret=merged,
                cas=current_version,  # Only succeeds if version matches
                mount_point='secret'
            )
            return True

        except hvac.exceptions.InvalidRequest as e:
            if 'check-and-set' in str(e).lower():
                # Version conflict, retry
                print(f"Conflict detected, retrying (attempt {attempt + 1})")
                continue
            raise

    raise RuntimeError("Failed to update secret after retries")
```

**Prevention:**
- Use KV v2 with Check-And-Set (CAS) parameter
- Implement retry logic with exponential backoff
- Coordinate updates through queue or lock
- Consider using a distributed lock for critical sections

---

### Gotcha: Stale Cached Data

**Symptom:**
Application uses old configuration despite vault being updated.

**Problem:**
```python
# Global cache without invalidation
_cache = {}

def get_secret(path):
    if path in _cache:
        return _cache[path]  # ❌ Never invalidated

    secret = vault.read(path)
    _cache[path] = secret
    return secret
```

**Solution:**
```python
from datetime import datetime, timedelta

_cache = {}
_cache_expiry = {}

def get_secret(path, ttl_seconds=300):
    now = datetime.utcnow()

    # Check cache and expiry
    if path in _cache:
        if path in _cache_expiry and now < _cache_expiry[path]:
            return _cache[path]

    # Cache miss or expired
    secret = vault.read(path)
    _cache[path] = secret
    _cache_expiry[path] = now + timedelta(seconds=ttl_seconds)

    return secret

def invalidate_cache(path=None):
    """Manually invalidate cache"""
    if path:
        _cache.pop(path, None)
        _cache_expiry.pop(path, None)
    else:
        _cache.clear()
        _cache_expiry.clear()
```

**Prevention:**
- Always use TTL-based caching
- Implement cache invalidation
- Consider using Redis for distributed caching
- Monitor cache hit/miss rates

---

## 6. Performance Issues

### Gotcha: Sequential Read Operations

**Symptom:**
Application startup takes minutes due to loading many secrets.

**Problem:**
```python
# Loading secrets sequentially
secrets = {}
for path in secret_paths:
    secrets[path] = vault.read(path)  # ❌ One at a time
# Total time: N * latency
```

**Solution:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_secrets_parallel(paths, max_workers=10):
    """Load multiple secrets in parallel"""
    secrets = {}
    errors = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(vault.read, path): path
            for path in paths
        }

        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                secrets[path] = future.result()
            except Exception as e:
                errors[path] = str(e)

    if errors:
        print(f"Failed to load {len(errors)} secrets: {errors}")

    return secrets

# Load all secrets in parallel
all_secrets = load_secrets_parallel(secret_paths, max_workers=20)
# Total time: ~latency (for slowest operation)
```

**Prevention:**
- Batch secret reads when possible
- Use parallel operations for independent reads
- Cache frequently accessed secrets
- Profile startup time and optimize

---

### Gotcha: Not Using KV v2 Batch Operations

**Symptom:**
Many API calls for related secrets.

**Problem:**
```python
# Loading related secrets one by one
db_host = vault.read('secret/data/db/host')
db_port = vault.read('secret/data/db/port')
db_user = vault.read('secret/data/db/user')
db_pass = vault.read('secret/data/db/password')
# 4 API calls for related data
```

**Solution:**
```python
# Group related secrets in one path
db_config = vault.read('secret/data/db/config')
# Single API call returns:
# {
#   'host': '...',
#   'port': '...',
#   'user': '...',
#   'password': '...'
# }

# Use structured data
host = db_config['data']['data']['host']
port = db_config['data']['data']['port']
```

**Prevention:**
- Design secret hierarchies logically
- Group related secrets together
- Document secret structure
- Use JSON schema for complex secrets

---

## 7. Logging and Debugging

### Gotcha: Secrets in Log Files

**Symptom:**
Security audit finds secrets in application logs.

**Problem:**
```python
# Accidentally logging secret values
secret = vault.read('secret/data/api-key')
logger.info(f"Loaded API key: {secret['data']['data']['key']}")  # ❌ Secret in logs!

# Or in error messages
try:
    vault.write(path, {'api_key': 'abc123'})
except Exception as e:
    logger.error(f"Failed to write: {e}")  # ❌ Might include secret in exception
```

**Solution:**
```python
# Sanitized logging
secret = vault.read('secret/data/api-key')
logger.info(
    "Loaded API key",
    extra={
        'path': 'secret/data/api-key',
        'key_exists': 'key' in secret['data']['data'],
        'key_length': len(secret['data']['data'].get('key', ''))
        # Never log the actual value
    }
)

# Sanitized error handling
try:
    vault.write(path, data)
except Exception as e:
    # Log error type and path, not data
    logger.error(
        f"Failed to write secret to {path}: {type(e).__name__}",
        exc_info=False  # Don't include full stack trace with data
    )
```

**Prevention:**
- Never log secret values
- Sanitize error messages
- Use structured logging with explicit fields
- Regular log audits for leaked secrets
- Implement log scrubbing if necessary

---

### Gotcha: Debugging with Print Statements

**Problem:**
```python
# During debugging
print(f"Secret data: {vault.read('secret/data/api')}")  # ❌ Printed to stdout/logs
```

**Solution:**
```python
# Use debug logging with appropriate levels
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Not DEBUG in production

# Instead of print
secret = vault.read('secret/data/api')
logger.debug("Secret structure: keys=%s", list(secret['data']['data'].keys()))
# Only shows keys, not values
```

**Prevention:**
- Remove debug prints before committing
- Use logging framework with levels
- Configure DEBUG level only in development
- Code review for print statements with secrets

---

## 8. Deployment and Environment Issues

### Gotcha: Different Vault Instances for Environments

**Symptom:**
Production deployment fails because it's pointing to dev vault.

**Problem:**
```python
# Hardcoded vault address
VAULT_ADDR = "https://vault-dev.example.com"
```

**Solution:**
```python
# Environment-specific configuration
import os

env = os.getenv('APP_ENV', 'development')

vault_configs = {
    'development': {
        'addr': 'http://localhost:8200',
        'verify': False
    },
    'staging': {
        'addr': 'https://vault-staging.example.com',
        'verify': True
    },
    'production': {
        'addr': 'https://vault.example.com',
        'verify': True
    }
}

config = vault_configs[env]
vault_client = hvac.Client(url=config['addr'], verify=config['verify'])
```

**Prevention:**
- Use environment-specific configuration
- Validate vault endpoint at startup
- Document vault endpoints for each environment
- Implement smoke tests post-deployment

---

### Gotcha: Missing Environment Variables in Container

**Symptom:**
Application fails to start in Docker/Kubernetes with "VAULT_TOKEN must be set".

**Problem:**
```dockerfile
# Dockerfile
FROM python:3.9
COPY . /app
CMD ["python", "app.py"]
# No environment variables passed
```

**Solution:**

**Docker:**
```bash
# Pass via command line
docker run -e VAULT_ADDR=$VAULT_ADDR -e VAULT_TOKEN=$VAULT_TOKEN myapp

# Or use env file
docker run --env-file .env.production myapp
```

**Kubernetes:**
```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: myapp
    image: myapp:latest
    env:
    - name: VAULT_ADDR
      value: "https://vault.example.com"
    - name: VAULT_TOKEN
      valueFrom:
        secretKeyRef:
          name: vault-token
          key: token
```

**Prevention:**
- Document required environment variables
- Fail fast if critical variables missing
- Use Kubernetes secrets for credentials
- Test container locally with same env vars

---

## Quick Reference: Common Error Messages

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| `permission denied` | Token expired or insufficient permissions | Check token validity and policies |
| `namespace not found` | Wrong namespace (Vault Enterprise) | Set `VAULT_NAMESPACE` correctly |
| `invalid path` | Wrong KV version path format | Use `data` in path for KV v2 |
| `certificate verify failed` | Self-signed cert or CA not trusted | Add CA cert or use `verify=False` (dev only) |
| `connection refused` | Vault not reachable | Check URL, network, firewall |
| `check-and-set parameter did not match` | Concurrent modification conflict | Retry with latest version |
| `invalid data format` | Wrong JSON structure for KV v2 | Wrap data in `{"data": {...}}` |
| `lease expired` | Dynamic secret TTL exceeded | Renew lease or re-request secret |

---

**Last Updated:** 2026-02-06
**Contribute:** Found a new gotcha? Document it here!
