# Vault State Manager Skill

**Domain:** `foundation`
**Version:** 1.0.0
**Status:** Production Ready

## Quick Start

This skill provides secure vault state management capabilities for reading, writing, and updating secrets without exposing sensitive values.

### Prerequisites

```bash
# Set required environment variables
export VAULT_ADDR="https://vault.example.com"
export VAULT_TOKEN="<your-token>"

# Optional
export VAULT_NAMESPACE="<namespace>"  # For Vault Enterprise
export VAULT_AUDIT_LOG_PATH="./logs/vault-audit.log"
```

### Basic Usage

**Python:**
```python
from vault_manager import VaultStateManager

# Initialize
vault = VaultStateManager()

# Read secret
config = vault.read_secret('myapp/config')

# Write secret
vault.write_secret('myapp/config', {
    'api_key': 'abc123',
    'database_url': 'postgresql://...'
})

# Update specific fields
vault.update_secret('myapp/config', {
    'api_key': 'new-key'
})
```

**Shell:**
```bash
# Read secret
./assets/vault-read-template.sh secret/data/myapp/config | jq '.data.data'

# Write secret
./assets/vault-write-template.sh secret/data/myapp/config \
  '{"data":{"api_key":"abc123","db_url":"postgresql://..."}}'
```

## Documentation Structure

- **[SKILL.md](./SKILL.md)** - Complete skill specification with blueprints and anti-patterns
- **[docs/patterns.md](./docs/patterns.md)** - Common integration patterns and examples
- **[docs/impact-checklist.md](./docs/impact-checklist.md)** - Security impact assessment checklist
- **[docs/gotchas.md](./docs/gotchas.md)** - Common pitfalls and troubleshooting guide

## Asset Templates

All templates are parameterized and require environment variables (never hardcoded secrets):

- `assets/vault-read-template.sh` - Bash script for secure secret reading
- `assets/vault-write-template.sh` - Bash script for secure secret writing
- `assets/vault_manager.py` - Python class with full CRUD operations

## Key Features

✅ **Secure by Default**
- No hardcoded secrets
- Environment-based authentication
- Audit logging for all operations
- TLS/SSL enforcement

✅ **Multi-User Aware**
- Conflict detection with Check-And-Set (CAS)
- Optimistic locking support
- User tracking in audit logs

✅ **Production Ready**
- Circuit breaker pattern
- Retry logic with exponential backoff
- Comprehensive error handling
- Token renewal support

✅ **Developer Friendly**
- Caching with TTL
- Batch operations
- Parallel secret loading
- Clear error messages

## Security Checklist

Before deploying, review:
- [ ] Environment variables set correctly
- [ ] No secrets in code or logs
- [ ] Audit logging configured
- [ ] TLS certificate validation enabled
- [ ] Appropriate access policies applied
- [ ] Token renewal mechanism in place

See [impact-checklist.md](./docs/impact-checklist.md) for complete assessment.

## Common Issues

| Issue | Solution |
|-------|----------|
| "permission denied" | Check token validity and policies |
| "invalid path" | Use correct KV v2 path format (with `data`) |
| Certificate errors | Add CA cert or fix vault certificate |
| Timeout errors | Increase `VAULT_OPERATION_TIMEOUT` |

See [gotchas.md](./docs/gotchas.md) for comprehensive troubleshooting.

## Architecture

```
vault_state_manager/
├── SKILL.md                    # Main specification
├── README.md                   # This file
├── assets/                     # Reusable templates
│   ├── vault-read-template.sh
│   ├── vault-write-template.sh
│   └── vault_manager.py
└── docs/                       # Supporting documentation
    ├── patterns.md             # Integration patterns
    ├── impact-checklist.md     # Security assessment
    └── gotchas.md              # Troubleshooting guide
```

## Best Practices

1. **Always use environment variables** - Never hardcode vault addresses or tokens
2. **Implement caching with TTL** - Reduce API calls while maintaining freshness
3. **Add circuit breakers** - Prevent cascading failures when vault is unavailable
4. **Batch operations** - Load multiple secrets in parallel when possible
5. **Rotate credentials regularly** - Implement automated rotation for long-lived secrets
6. **Audit everything** - Log all vault operations for security compliance
7. **Handle failures gracefully** - Provide fallback mechanisms
8. **Separate by environment** - Use different vault paths for dev/staging/production

## Anti-Patterns to Avoid

❌ Hardcoding secrets in code
❌ Storing secrets in plain text files
❌ Logging secret values
❌ Ignoring token expiration
❌ Assuming single-user access

See [SKILL.md](./SKILL.md#anti-patterns) for detailed examples.

## Support

For issues, questions, or contributions:
1. Review [gotchas.md](./docs/gotchas.md) for common problems
2. Check [patterns.md](./docs/patterns.md) for usage examples
3. Complete [impact-checklist.md](./docs/impact-checklist.md) for security review
4. Consult main [SKILL.md](./SKILL.md) for complete reference

---

**Maintained by:** Foundation Team
**Last Updated:** 2026-02-06
**License:** Internal Use Only
