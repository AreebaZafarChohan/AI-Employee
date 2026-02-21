#!/usr/bin/env python3
"""
example_usage.py
Demonstrates secure vault state management patterns
"""

import os
import sys
from typing import Dict, Any

# Import vault manager (adjust path as needed)
from vault_manager import VaultStateManager, VaultConfig


def example_basic_operations():
    """Example 1: Basic read/write/update operations"""
    print("=== Example 1: Basic Operations ===\n")

    try:
        # Initialize vault manager from environment
        vault = VaultStateManager()

        # Read secret
        print("Reading secret from vault...")
        config = vault.read_secret('myapp/config')

        if config:
            print(f"✓ Retrieved {len(config)} configuration keys")
            print(f"  Keys: {list(config.keys())}")
        else:
            print("⚠ Secret not found, creating new one...")

            # Write new secret
            vault.write_secret('myapp/config', {
                'api_key': 'example-api-key',
                'database_url': 'postgresql://localhost:5432/myapp',
                'debug_mode': False
            })
            print("✓ Secret created successfully")

        # Update specific field
        print("\nUpdating secret field...")
        vault.update_secret('myapp/config', {
            'last_updated': '2026-02-06',
            'version': '1.0.0'
        })
        print("✓ Secret updated successfully")

        # Read updated secret
        updated_config = vault.read_secret('myapp/config')
        print(f"✓ Updated config has {len(updated_config)} keys")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def example_environment_specific():
    """Example 2: Environment-specific configuration loading"""
    print("\n=== Example 2: Environment-Specific Config ===\n")

    env = os.getenv('APP_ENV', 'development')
    app_name = os.getenv('APP_NAME', 'myapp')

    print(f"Environment: {env}")
    print(f"Application: {app_name}")

    try:
        vault = VaultStateManager()

        # Load environment-specific secrets
        secret_path = f"{app_name}/{env}/config"
        print(f"\nLoading secrets from: {secret_path}")

        config = vault.read_secret(secret_path)

        if config:
            print(f"✓ Loaded configuration for {env}")
            # Never log actual values, only metadata
            print(f"  Configuration keys: {list(config.keys())}")
            print(f"  Has database config: {'database_url' in config}")
            print(f"  Has API keys: {'api_key' in config}")
        else:
            print(f"⚠ No configuration found for {env} environment")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)


def example_batch_loading():
    """Example 3: Batch loading multiple secrets"""
    print("\n=== Example 3: Batch Secret Loading ===\n")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    secret_paths = [
        'myapp/config',
        'myapp/api-keys',
        'myapp/database',
        'myapp/features'
    ]

    try:
        vault = VaultStateManager()

        print(f"Loading {len(secret_paths)} secrets in parallel...")

        results = {}
        errors = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all read operations
            future_to_path = {
                executor.submit(vault.read_secret, path): path
                for path in secret_paths
            }

            # Collect results
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    data = future.result()
                    if data:
                        results[path] = data
                        print(f"  ✓ {path}: {len(data)} keys")
                    else:
                        errors[path] = "not found"
                        print(f"  ⚠ {path}: not found")
                except Exception as e:
                    errors[path] = str(e)
                    print(f"  ✗ {path}: {e}")

        print(f"\n✓ Successfully loaded {len(results)}/{len(secret_paths)} secrets")

        if errors:
            print(f"⚠ Failed to load {len(errors)} secrets:")
            for path, error in errors.items():
                print(f"    - {path}: {error}")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)


def example_safe_defaults():
    """Example 4: Safe defaults and error handling"""
    print("\n=== Example 4: Safe Defaults & Error Handling ===\n")

    try:
        vault = VaultStateManager()

        # Read with safe fallback
        config = vault.read_secret('myapp/config')

        # Provide safe defaults for missing secrets
        api_key = None
        if config:
            api_key = config.get('api_key')

        if not api_key:
            print("⚠ API key not found in vault")

            # Check environment variable fallback (dev only)
            if os.getenv('APP_ENV') == 'development':
                api_key = os.getenv('DEV_API_KEY', 'dev-key-placeholder')
                print("  → Using development fallback from environment")
            else:
                print("  ✗ CRITICAL: API key required but not found")
                sys.exit(1)

        # Never log actual secret value
        print(f"✓ API key configured (length: {len(api_key) if api_key else 0})")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)


def example_caching():
    """Example 5: Caching with TTL"""
    print("\n=== Example 5: Caching Strategy ===\n")

    from datetime import datetime, timedelta

    class CachedVaultManager:
        def __init__(self, vault: VaultStateManager, ttl_seconds: int = 300):
            self.vault = vault
            self.ttl_seconds = ttl_seconds
            self._cache = {}
            self._cache_time = {}

        def read_secret(self, path: str) -> Dict[str, Any]:
            now = datetime.utcnow()

            # Check cache
            if path in self._cache:
                cached_time = self._cache_time[path]
                age = (now - cached_time).total_seconds()

                if age < self.ttl_seconds:
                    print(f"  [CACHE HIT] {path} (age: {age:.1f}s)")
                    return self._cache[path]
                else:
                    print(f"  [CACHE EXPIRED] {path} (age: {age:.1f}s)")

            # Cache miss - fetch from vault
            print(f"  [CACHE MISS] {path} - fetching from vault")
            data = self.vault.read_secret(path)

            if data:
                self._cache[path] = data
                self._cache_time[path] = now

            return data

    try:
        base_vault = VaultStateManager()
        cached_vault = CachedVaultManager(base_vault, ttl_seconds=300)

        print("First read (cache miss):")
        config1 = cached_vault.read_secret('myapp/config')

        print("\nSecond read (cache hit):")
        config2 = cached_vault.read_secret('myapp/config')

        print("\nThird read (cache hit):")
        config3 = cached_vault.read_secret('myapp/config')

        print(f"\n✓ Cache working correctly")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)


def main():
    """Run all examples"""
    print("Vault State Manager - Example Usage")
    print("=" * 50)

    # Check environment
    if not os.getenv('VAULT_ADDR') or not os.getenv('VAULT_TOKEN'):
        print("\n✗ Error: VAULT_ADDR and VAULT_TOKEN must be set")
        print("\nSet environment variables:")
        print("  export VAULT_ADDR=https://vault.example.com")
        print("  export VAULT_TOKEN=<your-token>")
        sys.exit(1)

    # Run examples
    try:
        example_basic_operations()
        example_environment_specific()
        example_batch_loading()
        example_safe_defaults()
        example_caching()

        print("\n" + "=" * 50)
        print("✓ All examples completed successfully")

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
