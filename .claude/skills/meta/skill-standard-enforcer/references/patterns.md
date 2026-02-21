# Reference: Patterns

This document describes the patterns used in skill creation, when to use them, when to avoid them, and their tradeoffs.

---

## Pattern 1: Parameterized Configuration

### What It Is

Using `{{VARIABLE_NAME}}` placeholders instead of hardcoded values in all configuration files and templates.

### When to Use

- **Always** - This is the default pattern for all skills
- Configuration files (Dockerfiles, docker-compose.yml, k8s manifests)
- Application config (JSON, YAML, INI files)
- Environment files (.env.example)
- CI/CD pipeline definitions

### When NOT to Use

- Actual `.env` files (these should have real values)
- Generated/compiled artifacts
- Documentation examples (use realistic examples instead)
- Temporary debug files

### Tradeoffs

**Pros:**
- ✅ Environment-agnostic templates
- ✅ Single source of truth for configuration
- ✅ Easy to override per environment
- ✅ Clear documentation of required variables
- ✅ Prevents accidental credential commits

**Cons:**
- ❌ Requires rendering step before use
- ❌ More complex than hardcoded values
- ❌ Template engine dependency

---

## Pattern 2: Environment-Specific Overlays

### What It Is

Creating base configuration with environment-specific override files:

```
config/
├── base.yml              # Common settings
├── development.yml       # Dev overrides
├── staging.yml           # Staging overrides
└── production.yml        # Prod overrides
```

### When to Use

- Multi-environment deployments (local, dev, staging, prod)
- Significant differences between environments
- Need to test different configurations in same code
- Complex applications with 3+ environments

### When NOT to Use

- Single environment applications
- Simple configurations (use simple `.env` instead)
- When environments differ only in secrets

### Tradeoffs

**Pros:**
- ✅ Clear separation of environment concerns
- ✅ Type-safe configuration validation
- ✅ Can test production configs locally
- ✅ Version-controlled configuration differences

**Cons:**
- ❌ More files to manage
- ❌ YAML merging complexity
- ❌ Learning curve for new developers
- ❌ Risk of configuration drift between environments

---

## Pattern 3: Service Discovery via DNS

### What It Is

Using service names instead of IP addresses or localhost:

```yaml
# WRONG
DATABASE_HOST: localhost
CACHE_HOST: 127.0.0.1

# CORRECT
DATABASE_HOST: postgres-service
CACHE_HOST: redis-service
```

### When to Use

- Containerized environments (Docker, Kubernetes)
- Microservices architecture
- Multiple services communicating over network
- Any distributed system

### When NOT to Use

- Single monolithic applications
- True localhost development (no containers)
- Embedded systems without networking

### Tradeoffs

**Pros:**
- ✅ Works seamlessly in containers
- ✅ Automatic load balancing (in K8s)
- ✅ Service scaling transparent to consumers
- ✅ No IP address management needed

**Cons:**
- ❌ Requires container orchestration (Docker Compose/K8s)
- ❌ Localhost development setup more complex
- ❌ Debugging network issues harder
- ❌ External services need special configuration

**Variable Strategy:**
```yaml
# Per environment mapping
local: DATABASE_HOST=localhost
docker: DATABASE_HOST=postgres
k8s: DATABASE_HOST=postgres-service
prod: DATABASE_HOST=db.prod.company.com
```

---

## Pattern 4: Secret Externalization

### What It Is

Never hardcoding secrets in templates, images, or repositories.

```yaml
# WRONG - Secrets in Dockerfile
ENV DATABASE_PASSWORD="actual_password"

# CORRECT - Secrets at runtime
ENV DATABASE_PASSWORD=""
# Then set via: docker run -e DATABASE_PASSWORD=$DB_PASS
```

### When to Use

- **Always** - This is mandatory
- Database credentials
- API keys
- JWT secrets
- OAuth client secrets
- Encryption keys
- Private certificates

### When NOT to Use

**Never** - There is no valid case for hardcoding secrets

### Tradeoffs

**Pros:**
- ✅ Prevents secret leakage in code repositories
- ✅ Different secrets per environment
- ✅ Easy secret rotation without code changes
- ✅ Audit trail of secret access
- ✅ Meets security compliance requirements

**Cons:**
- ❌ More complex deployment process
- ❌ Requires secret management infrastructure
- ❌ Risk of misconfiguration
- ❌ Local development setup overhead

**Implementation Options:**

1. **Environment Variables** (simple, suitable for local/dev)
   ```bash
   export DATABASE_PASSWORD="..."
   ```

2. **Docker Secrets** (Docker Swarm)
   ```bash
   echo "password" | docker secret create db_pass -
   ```

3. **Kubernetes Secrets** (K8s)
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: db-credentials
   type: Opaque
   data:
     password: cGFzc3dvcmQ=  # base64 encoded
   ```

4. **Vault / Secrets Manager** (production)
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Google Secret Manager

---

## Pattern 5: Health Check Endpoints

### What It Is

Exposing HTTP endpoints for orchestrators to verify service health:

```javascript
// Liveness probe: Is the service running?
app.get('/health/live', (req, res) => {
  res.status(200).json({ status: 'alive' });
});

// Readiness probe: Is the service ready to receive traffic?
app.get('/health/ready', async (req, res) => {
  try {
    await db.ping();
    await cache.ping();
    res.status(200).json({ status: 'ready' });
  } catch (err) {
    res.status(503).json({ status: 'not ready' });
  }
});
```

### When to Use

- Containerized applications (Docker, Kubernetes)
- Load balancer backends
- Services with startup dependencies
- Production environments with uptime requirements

### When NOT to Use

- Short-lived batch jobs
- Command-line utilities
- Applications without HTTP server
- Development-only scripts

### Tradeoffs

**Pros:**
- ✅ Kubernetes can restart unhealthy pods automatically
- ✅ Load balancers route to healthy instances only
- ✅ Clear signal of service readiness
- ✅ Graceful startup and shutdown

**Cons:**
- ❌ Additional code complexity
- ❌ Slightly increased resource usage
- ❌ False positives if checks are too simple
- ❌ False negatives if checks are too strict

**Configuration Pattern:**
```yaml
# In docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:{{PORT}}/health/ready"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## Pattern 6: Graceful Degradation

### What It Is

Service continues operating when optional dependencies fail:

```javascript
// Cache is optional, app works without it
let cache = null;
try {
  cache = await connectToRedis();
  console.log('Cache connected');
} catch (err) {
  console.warn('Cache unavailable, operating without cache');
}

// Use cache if available, otherwise fetch from DB
async function getUser(id) {
  if (cache) {
    const cached = await cache.get(`user:${id}`);
    if (cached) return JSON.parse(cached);
  }

  const user = await db.query('SELECT * FROM users WHERE id = ?', [id]);

  if (cache) {
    await cache.set(`user:${id}`, JSON.stringify(user), 'EX', 3600);
  }

  return user;
}
```

### When to Use

- Optional dependencies (cache, search, analytics)
- Non-critical features
- High availability requirements
- Third-party services that may be down

### When NOT to Use

- Critical dependencies (database, core services)
- Data consistency requirements
- Financial transactions
- Safety-critical systems

### Tradeoffs

**Pros:**
- ✅ Higher availability (partial failures tolerated)
- ✅ Better user experience (slow vs down)
- ✅ Reduced operational burden
- ✅ Easier maintenance windows

**Cons:**
- ❌ More complex code (null checks everywhere)
- ❌ Harder to test (must test with and without dependency)
- ❌ Risk of masking real problems
- ❌ Circuit breaker logic adds complexity

**Circuit Breaker Pattern:**
```javascript
// After N failures, stop trying for a period
let circuitOpen = false;
let failureCount = 0;
const FAILURE_THRESHOLD = 5;
const CIRCUIT_TIMEOUT = 60000; // 1 minute

async function callExternalService() {
  if (circuitOpen) {
    throw new Error('Circuit breaker open');
  }

  try {
    const result = await externalService.call();
    failureCount = 0;  // Reset on success
    return result;
  } catch (err) {
    failureCount++;
    if (failureCount >= FAILURE_THRESHOLD) {
      circuitOpen = true;
      setTimeout(() => {
        circuitOpen = false;
        failureCount = 0;
      }, CIRCUIT_TIMEOUT);
    }
    throw err;
  }
}
```

---

## Pattern 7: Structured Logging

### What It Is

Using JSON or structured format instead of plain text logs:

```javascript
// WRONG - Plain text
console.log(`User ${userId} logged in at ${new Date()}`);

// CORRECT - Structured JSON
console.log(JSON.stringify({
  timestamp: new Date().toISOString(),
  level: 'info',
  message: 'User logged in',
  userId: userId,
  action: 'login'
}));
```

### When to Use

- Production services
- Microservices architecture
- Centralized logging systems (ELK, Splunk)
- Cloud deployments (AWS CloudWatch, Google Stackdriver)
- Any environment requiring log aggregation

### When NOT to Use

- Local development (plain text is more readable)
- Simple CLI tools
- One-off scripts
- When directly reading logs (not using log aggregator)

### Tradeoffs

**Pros:**
- ✅ Machine-readable, easy to parse
- ✅ Consistent log format across services
- ✅ Rich context in log entries
- ✅ Easy filtering and searching
- ✅ Integration with log aggregation tools

**Cons:**
- ❌ Harder to read manually
- ❌ Verbosity (more bytes per log line)
- ❌ Requires log aggregation tool for analysis
- ❌ Library dependencies for structured logging

**Recommended Fields:**
```javascript
{
  "timestamp": "2023-10-01T12:00:00.000Z",  // ISO 8601
  "level": "info|warn|error|debug",        // Log level
  "message": "Clear description",          // Human-readable
  "service": "service-name",               // Service identifier
  "environment": "production|staging",     // Environment name
  "traceId": "uuid",                       // Distributed tracing ID
  "userId": "user-identifier",             // User context (if applicable)
  "error": { ... },                        // Error details (if applicable)
  "durationMs": 123,                       // Duration for requests
  "statusCode": 200                        // HTTP status (for APIs)
}
```

---

## Pattern 8: Multi-Stage Docker Builds

### What It Is

Using multiple `FROM` statements to optimize final image:

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Runtime stage (smaller)
FROM node:18-alpine AS runtime
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
USER node
CMD ["node", "dist/server.js"]
```

### When to Use

- Compiled languages (Go, Java, Rust, TypeScript)
- Applications with build dependencies
- Need to minimize production image size
- Security-sensitive environments

### When NOT to Use

- Interpreted languages without build step (Python, Ruby)
- Simple applications without dependencies
- When image size doesn't matter
- Development images (want build tools included)

### Tradeoffs

**Pros:**
- ✅ Significantly smaller final image
- ✅ Reduced attack surface (fewer installed packages)
- ✅ Faster production deployments
- ✅ Build dependencies not in production

**Cons:**
- ❌ More complex Dockerfile
- ❌ Longer build time (multiple stages)
- ❌ Harder to debug production image
- ❌ Layer cache less effective

**Size Comparison:**
```
Standard Node.js app:
- Single stage: ~1.2 GB
- Multi-stage: ~200 MB
- Reduction: 83% smaller
```

---

## Pattern 9: Version Pinning

### What It Is

Specifying exact versions for dependencies:

```dockerfile
# WRONG - Latest versions
FROM node:latest
RUN npm install express

# CORRECT - Pinned versions
FROM node:18.18.0-alpine3.18
RUN npm install express@4.18.2
```

### When to Use

- **Production** - Always
- Reproducible builds required
- Stability over latest features
- Team collaboration (consistent environments)
- CI/CD pipelines

### When NOT to Use

- Prototype/POC development
- Want automatic security updates
- Testing compatibility with new versions
- Personal projects without team

### Tradeoffs

**Pros:**
- ✅ Reproducible builds (same code = same result)
- ✅ Prevents unexpected breaking changes
- ✅ Consistent across all environments
- ✅ Deterministic dependency tree

**Cons:**
- ❌ Manual update process
- ❌ Miss security patches automatically
- ❌ Can fall behind on features
- ❌ Maintenance burden to keep updated

**Tools:**
- JavaScript: `package-lock.json`, exact versions in `package.json`
- Python: `requirements.txt` with `==`
- Docker: SHA256 digests for immutability
- Rust: `Cargo.lock` committed to repo

---

## Pattern 10: Non-Root Container Execution

### What It Is

Running container as non-root user:

```dockerfile
# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# Switch to non-root user
USER nodejs

# Now run application
CMD ["node", "server.js"]
```

### When to Use

- **All production containers** - Mandatory security practice
- Multi-tenant environments
- Restricted security contexts
- Compliance requirements

### When NOT to Use

- Development containers (convenience)
- When root privileges genuinely required (rare)
- Legacy applications that can't run as non-root
- System containers (init, monitoring)

### Tradeoffs

**Pros:**
- ✅ Security: Container escape is harder
- ✅ Compliance: Meets security benchmarks
- ✅ Defense in depth
- ✅ Follows principle of least privilege

**Cons:**
- ❌ Permission issues with mounted volumes
- ❌ Can't bind to privileged ports (< 1024)
- ❌ Limited system operations
- ❌ Some tools require root

**Solutions:**
```dockerfile
# Use unprivileged ports
EXPOSE 3000  # Not 80, 443

# Handle volume permissions
RUN mkdir /app && chown -R nodejs:nodejs /app
WORKDIR /app

# Init Containers (K8s) can set permissions before app starts
```

---

## Pattern Selection Guide

| Pattern | Complexity | When to Use | Priority |
|---------|-----------|-------------|----------|
| Parameterized Config | Low | Always | Critical |
| Service Discovery | Medium | Containers/K8s | High |
| Secret Externalization | Medium | Always | Critical |
| Health Checks | Low | Production | High |
| Graceful Degradation | High | Optional deps | Medium |
| Structured Logging | Medium | Production | High |
| Multi-Stage Builds | High | Compiled langs | Medium |
| Version Pinning | Low | Production | High |
| Non-Root User | Low | All containers | Critical |

---

## Anti-Pattern Equivalents

| Anti-Pattern | Pattern Replacement | Severity |
|--------------|---------------------|----------|
| Hardcoded `localhost` | Service Discovery | Critical |
| Hardcoded secrets | Secret Externalization | Critical |
| Fixed ports | Parameterized Config | High |
| No health checks | Health Endpoints | High |
| No error handling | Graceful Degradation | Medium |
| Plain text logs | Structured Logging | Medium |
| Latest version tags | Version Pinning | High |
| Root user | Non-Root User | Critical |

---
