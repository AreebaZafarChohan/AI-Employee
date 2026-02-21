# Vault State Manager - Common Patterns

## Overview
This document describes common integration patterns for the Vault State Manager skill across different use cases and environments.

---

## Pattern 1: Application Configuration Loading

### Use Case
Load application configuration secrets at startup from vault.

### Implementation

```python
from vault_manager import VaultStateManager, VaultConfig

class AppConfig:
    """Application configuration loaded from vault"""

    def __init__(self, env: str = 'production'):
        self.env = env
        self.vault = VaultStateManager()
        self._config = {}

    def load(self):
        """Load all configuration from vault"""
        base_path = f"app/{self.env}"

        # Load database config
        self._config['database'] = self.vault.read_secret(f"{base_path}/database")

        # Load API keys
        self._config['api_keys'] = self.vault.read_secret(f"{base_path}/api-keys")

        # Load external service credentials
        self._config['services'] = self.vault.read_secret(f"{base_path}/services")

        return self._config

    def get(self, key: str, default=None):
        """Get configuration value by key"""
        return self._config.get(key, default)

# Usage
config = AppConfig(env='production')
config.load()

db_url = config.get('database', {}).get('url')
api_key = config.get('api_keys', {}).get('stripe')
```

### Benefits
- Centralized configuration management
- Environment-specific configuration
- Audit trail of configuration access
- No secrets in environment variables or files

---

## Pattern 2: Dynamic Secret Rotation

### Use Case
Automatically rotate database credentials on a schedule.

### Implementation

```python
import schedule
import time
from datetime import datetime, timedelta
from vault_manager import VaultStateManager

class CredentialRotator:
    """Rotate credentials automatically"""

    def __init__(self, vault: VaultStateManager):
        self.vault = vault

    def rotate_database_password(self, db_path: str):
        """Rotate database password"""
        # Generate new password
        new_password = self._generate_secure_password()

        # Update in database
        self._update_database_user_password(new_password)

        # Update in vault
        self.vault.update_secret(db_path, {
            'password': new_password,
            'rotated_at': datetime.utcnow().isoformat(),
            'next_rotation': (datetime.utcnow() + timedelta(days=90)).isoformat()
        })

        print(f"Rotated password for {db_path}")

    def _generate_secure_password(self, length: int = 32) -> str:
        """Generate cryptographically secure password"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def _update_database_user_password(self, new_password: str):
        """Update password in actual database"""
        # Implementation depends on database type
        pass

# Usage
rotator = CredentialRotator(VaultStateManager())

# Schedule rotation every 90 days
schedule.every(90).days.do(
    rotator.rotate_database_password,
    db_path='production/database/main'
)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

---

## Pattern 3: Multi-Environment Configuration

### Use Case
Manage secrets across multiple environments (dev, staging, production) with appropriate access controls.

### Implementation

```bash
#!/usr/bin/env bash
# setup-multi-env-secrets.sh

set -euo pipefail

ENVIRONMENTS=("dev" "staging" "production")
APP_NAME="myapp"

setup_environment_secrets() {
    local env="$1"
    local base_path="$APP_NAME/$env"

    echo "Setting up secrets for environment: $env"

    # Database credentials
    vault kv put "secret/$base_path/database" \
        host="db-$env.example.com" \
        port="5432" \
        username="app_user_$env" \
        password="$(generate_password)" \
        database="$APP_NAME-$env"

    # API keys (different per environment)
    vault kv put "secret/$base_path/api-keys" \
        stripe_key="sk_${env}_$(generate_api_key)" \
        sendgrid_key="SG.$(generate_api_key)" \
        datadog_key="$(generate_api_key)"

    # External services
    vault kv put "secret/$base_path/services" \
        redis_url="redis://$env-redis.example.com:6379" \
        s3_bucket="$APP_NAME-$env-assets"

    # Set up policies for environment
    vault policy write "$APP_NAME-$env-read" - <<EOF
path "secret/data/$base_path/*" {
  capabilities = ["read", "list"]
}
EOF

    echo "✓ Completed setup for $env"
}

generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

generate_api_key() {
    openssl rand -hex 16
}

# Setup all environments
for env in "${ENVIRONMENTS[@]}"; do
    setup_environment_secrets "$env"
done

echo "All environments configured successfully"
```

### Access Pattern

```python
import os
from vault_manager import VaultStateManager

# Determine environment from ENV variable
env = os.getenv('APP_ENV', 'dev')

vault = VaultStateManager()
config = vault.read_secret(f"myapp/{env}/database")

print(f"Loaded config for {env} environment")
```

---

## Pattern 4: Caching with TTL

### Use Case
Reduce vault API calls by caching secrets with appropriate TTL.

### Implementation

```python
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from vault_manager import VaultStateManager

@dataclass
class CachedSecret:
    """Cached secret with expiration"""
    data: Dict[str, Any]
    cached_at: datetime
    ttl_seconds: int

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        expiry = self.cached_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry


class CachedVaultManager:
    """Vault manager with caching support"""

    def __init__(self, vault: VaultStateManager, default_ttl: int = 300):
        self.vault = vault
        self.default_ttl = default_ttl  # 5 minutes default
        self._cache: Dict[str, CachedSecret] = {}

    def read_secret(self, path: str, ttl: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Read secret with caching"""
        # Check cache first
        if path in self._cache:
            cached = self._cache[path]
            if not cached.is_expired():
                return cached.data

        # Cache miss or expired - fetch from vault
        data = self.vault.read_secret(path)
        if data:
            self._cache[path] = CachedSecret(
                data=data,
                cached_at=datetime.utcnow(),
                ttl_seconds=ttl or self.default_ttl
            )

        return data

    def invalidate_cache(self, path: Optional[str] = None):
        """Invalidate cache for specific path or all"""
        if path:
            self._cache.pop(path, None)
        else:
            self._cache.clear()

    def write_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Write secret and invalidate cache"""
        success = self.vault.write_secret(path, data)
        if success:
            self.invalidate_cache(path)
        return success


# Usage
vault = CachedVaultManager(VaultStateManager(), default_ttl=600)

# First call hits vault
config = vault.read_secret('myapp/config')  # Vault API call

# Subsequent calls use cache (within TTL)
config = vault.read_secret('myapp/config')  # From cache
config = vault.read_secret('myapp/config')  # From cache

# Write invalidates cache
vault.write_secret('myapp/config', {'new': 'data'})

# Next read hits vault again
config = vault.read_secret('myapp/config')  # Vault API call
```

---

## Pattern 5: Circuit Breaker for Vault Operations

### Use Case
Prevent cascading failures when vault is unavailable.

### Implementation

```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker pattern for vault operations"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise RuntimeError("Circuit breaker is OPEN - vault unavailable")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        self.success_count = 0

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True

        timeout = timedelta(seconds=self.timeout_seconds)
        return datetime.utcnow() - self.last_failure_time > timeout


# Usage
from vault_manager import VaultStateManager

vault = VaultStateManager()
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout_seconds=60,
    success_threshold=2
)

def safe_read_secret(path: str):
    """Read secret with circuit breaker protection"""
    try:
        return circuit_breaker.call(vault.read_secret, path)
    except RuntimeError as e:
        # Circuit is open, use fallback
        print(f"Vault unavailable: {e}")
        return load_fallback_config()

def load_fallback_config():
    """Fallback configuration when vault is unavailable"""
    # Return cached config or minimal safe defaults
    return {'fallback': True}


# Application code
config = safe_read_secret('myapp/config')
```

---

## Pattern 6: Batch Secret Loading

### Use Case
Load multiple secrets efficiently in a single operation.

### Implementation

```python
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from vault_manager import VaultStateManager

class BatchVaultLoader:
    """Load multiple secrets in parallel"""

    def __init__(self, vault: VaultStateManager, max_workers: int = 5):
        self.vault = vault
        self.max_workers = max_workers

    def load_secrets(self, paths: List[str]) -> Dict[str, Any]:
        """Load multiple secrets in parallel"""
        results = {}
        errors = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all read operations
            future_to_path = {
                executor.submit(self.vault.read_secret, path): path
                for path in paths
            }

            # Collect results
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    data = future.result()
                    if data:
                        results[path] = data
                    else:
                        errors[path] = "Secret not found"
                except Exception as e:
                    errors[path] = str(e)

        if errors:
            print(f"Failed to load {len(errors)} secrets: {errors}")

        return results


# Usage
vault = VaultStateManager()
loader = BatchVaultLoader(vault, max_workers=10)

# Load multiple secrets at once
secret_paths = [
    'myapp/production/database',
    'myapp/production/api-keys',
    'myapp/production/services',
    'myapp/production/feature-flags'
]

all_secrets = loader.load_secrets(secret_paths)

print(f"Loaded {len(all_secrets)} secrets successfully")
```

---

## Best Practices Summary

1. **Always Use Environment Variables** - Never hardcode vault addresses or tokens
2. **Implement Caching** - Reduce API calls with appropriate TTL
3. **Add Circuit Breakers** - Prevent cascading failures
4. **Batch Operations** - Load multiple secrets in parallel when possible
5. **Rotate Credentials** - Implement automated rotation for long-lived secrets
6. **Audit Everything** - Log all vault operations for security compliance
7. **Handle Failures Gracefully** - Provide fallback mechanisms
8. **Separate by Environment** - Use different vault paths for dev/staging/production
9. **Version Secrets** - Use KV v2 for automatic versioning
10. **Monitor Performance** - Track latency and error rates

---

**Last Updated:** 2026-02-06
