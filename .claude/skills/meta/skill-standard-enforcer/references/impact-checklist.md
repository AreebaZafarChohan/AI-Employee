# Impact Checklist

This checklist must be completed for every skill before creation. For each category, verify all items and document findings.

---

## Environment Variables Checklist

### Variable Discovery

- [ ] **Identify all environment variables**
  - [ ] Searched codebase: `grep -r "process.env" src/`
  - [ ] Searched configs: `grep -r "getenv\|os.environ" . --include="*.py" --include="*.sh"`
  - [ ] Reviewed documentation for documented variables
  - [ ] Checked example env files: `.env.example`, `env.example`

- [ ] **Classify variables by type**
  - [ ] Build-time only (e.g., `BUILD_VERSION`, `BUILD_SHA`)
  - [ ] Runtime required (e.g., `DATABASE_URL`, `PORT`)
  - [ ] Runtime optional (e.g., `LOG_LEVEL`, `FEATURE_FLAG`)
  - [ ] Secrets (e.g., `API_KEY`, `DATABASE_PASSWORD`)

- [ ] **Define default values**
  - [ ] Non-sensitive variables have safe defaults
  - [ ] Secrets have NO defaults (always external)
  - [ ] Port variables use non-conflicting defaults
  - [ ] Boolean flags default to secure settings

- [ ] **Document variable purpose**
  - [ ] Each variable has clear description
  - [ ] Valid values/ranges documented
  - [ ] Environment-specific values noted
  - [ ] Example values provided (no real secrets)

### Variable Naming

- [ ] **Consistent naming convention**
  - [ ] Use `UPPER_SNAKE_CASE`
  - [ ] Service names are clear (`DATABASE_`, `CACHE_`, `API_`)
  - [ ] No ambiguous abbreviations
  - [ ] Related variables share prefix

- [ ] **Avoid naming conflicts**
  - [ ] Check for reserved names (`HOME`, `PATH`, `USER`)
  - [ ] Check for framework-specific names
  - [ ] Verify uniqueness across all services

### Secret Management

- [ ] **Secret classification**
  - [ ] All secrets identified and marked as `{{SECRET_*}}`
  - [ ] No secrets in repository (check `git history`)
  - [ ] No secrets in Docker images (check `docker history`)
  - [ ] No secrets in CI logs (check build output)

- [ ] **Secret storage strategy**
  - [ ] Local dev: documented `.env` file setup
  - [ ] Docker Compose: `.env` file mounted
  - [ ] Docker Swarm: docker secrets
  - [ ] Kubernetes: k8s secrets or external provider
  - [ ] Production: vault / cloud secrets manager

- [ ] **Secret rotation plan**
  - [ ] Documented rotation frequency
  - [ ] Zero-downtime rotation process
  - [ ] Versioning strategy for secrets
  - [ ] Audit trail for secret access

### Build-Time vs Runtime Separation

- [ ] **Build variables**
  - [ ] Only used during image build
  - [ ] Set in Dockerfile `ARG` instructions
  - [ ] Not needed at container runtime
  - [ ] Examples: `BUILD_TARGET`, `BUILD_VERSION`

- [ ] **Runtime variables**
  - [ ] Needed when container runs
  - [ ] Set via `ENV` or at runtime (`-e`, ConfigMap, etc.)
  - [ ] Cannot be baked into image
  - [ ] Examples: `DATABASE_URL`, `API_KEYS`

- [ ] **No mixed usage**
  - [ ] Build variables don't affect runtime behavior
  - [ ] Runtime variables can override build settings
  - [ ] Clear documentation of when each is used

---

## Network & Topology Checklist

### Port Analysis

- [ ] **Identify all exposed ports**
  - [ ] Application HTTP/HTTPS port(s)
  - [ ] Debug/metrics ports (e.g., 9090 for Prometheus)
  - [ ] Admin/management ports
  - [ ] Custom protocol ports

- [ ] **For each port, document:**
  - [ ] Internal port (container listens on)
  - [ ] External port (host/service exposes)
  - [ ] Protocol (TCP, UDP, HTTP/2, gRPC)
  - [ ] Purpose (web, API, metrics, health)
  - [ ] Security (public, internal-only, authenticated)

- [ ] **Port conflicts**
  - [ ] Check default port usage (3000, 8000, 8080, 5000)
  - [ ] Verify no conflicts in common services
  - [ ] Document alternative ports
  - [ ] Parameterize port in templates

### Localhost Detection

- [ ] **Scan for localhost usage**
  ```bash
  grep -r "localhost" . --include="*.js" --include="*.py" --include="*.yaml" --include="*.yml" --include="*.json"
  grep -r "127\.0\.0\.1" . --include="*.js" --include="*.py" --include="*.yaml" --include="*.yml" --include="*.json"
  ```

- [ ] **Map localhost to service names**
  - [ ] Database: `localhost:5432` → `{{DATABASE_HOST}}:5432`
  - [ ] Cache: `localhost:6379` → `{{CACHE_HOST}}:6379`
  - [ ] Search: `localhost:9200` → `{{SEARCH_HOST}}:9200`
  - [ ] Queue: `localhost:5672` → `{{QUEUE_HOST}}:5672`
  - [ ] API: `localhost:3000` → `{{API_SERVICE_NAME}}:3000`

- [ ] **Verify service name configuration**
  - [ ] Service names set in docker-compose.yml
  - [ ] Service names set in k8s service definitions
  - [ ] Code uses environment variables for hosts
  - [ ] Fallback behavior documented

### Dependency Topology

- [ ] **Map service dependencies**
  ```
  Service: web
  - Database (postgres) - REQUIRED
  - Cache (redis) - OPTIONAL
  - Search (elasticsearch) - OPTIONAL
  - Message Queue (rabbitmq) - OPTIONAL
  ```

- [ ] **Define startup order**
  - [ ] Critical dependencies start first (databases)
  - [ ] Application waits for dependencies
  - [ ] Optional dependencies don't block startup
  - [ ] Health checks confirm readiness

- [ ] **Network policies**
  - [ ] Document which services can call this service
  - [ ] Document which services this service calls
  - [ ] Internal vs external access patterns
  - [ ] Protocol requirements (HTTP/2, WebSockets, gRPC)

- [ ] **Resilience patterns**
  - [ ] Circuit breakers for external calls
  - [ ] Timeouts configured for all network calls
  - [ ] Retry logic with exponential backoff
  - [ ] Graceful degradation documented

---

## Auth / CORS / Security Impact Checklist

### Authentication Pattern

- [ ] **Identify authentication mechanism**
  - [ ] JWT tokens (stateless)
  - [ ] Session cookies (stateful)
  - [ ] OAuth 2.0 / OpenID Connect
  - [ ] API Keys
  - [ ] Mutual TLS (mTLS)
  - [ ] No authentication (public endpoints)

- [ ] **Auth configuration variables**
  - [ ] `JWT_SECRET` or `JWT_PUBLIC_KEY`
  - [ ] `SESSION_SECRET`
  - [ ] `OAUTH_CLIENT_ID`
  - [ ] `OAUTH_CLIENT_SECRET` (mark as secret!)
  - [ ] `API_KEY_HEADER_NAME`

- [ ] **Auth provider setup**
  - [ ] Documented callback URLs
  - [ ] Provider configuration steps
  - [ ] Required scopes/permissions
  - [ ] Token expiration and refresh

### CORS Configuration

- [ ] **Identify CORS requirements**
  - [ ] Is this a web API accessed from browsers?
  - [ ] List of allowed origins per environment
  - [ ] Credentials support needed?
  - [ ] Preflight cache duration

- [ ] **Environment-specific origins**
  - [ ] Local: `http://localhost:3000`
  - [ ] Docker: `http://localhost:3000`
  - [ ] Staging: `https://staging.{{APP_DOMAIN}}`
  - [ ] Production: `https://{{APP_DOMAIN}}`

- [ ] **Origin configuration pattern**
  ```yaml
  CORS_ORIGIN: "{{CORS_ALLOWED_ORIGINS}}"  # Comma-separated
  CORS_CREDENTIALS: "{{CORS_ALLOW_CREDENTIALS}}"
  ```

- [ ] **Security considerations**
  - [ ] No wildcard `*` with credentials allowed
  - [ ] Origin list strict (no regex with broad patterns)
  - [ ] Credentials require explicit origin list
  - [ ] Document any CORS proxies

### Callback URL Changes

- [ ] **List all callback URLs**
  - [ ] OAuth callback URLs
  - [ ] Webhook endpoints
  - [ ] Redirect URLs after auth
  - [ ] Payment provider callbacks

- [ **Per environment URL mapping**
  ```
  Local: http://localhost:8000/auth/callback
  Docker: http://web:8000/auth/callback
  K8s: http://web-service:8000/auth/callback
  Prod: https://{{APP_DOMAIN}}/auth/callback
  ```

- [ ] **Provider registration**
  - [ ] All callback URLs registered with providers
  - [ ] Document which providers need registration
  - [ ] Process for adding new callback URLs
  - [ ] Testing strategy for callbacks

### NODE_ENV Behavior

- [ ] **Define NODE_ENV values**
  - [ ] `development` - Debug mode, detailed errors
  - [ ] `production` - Optimized, minimal error details
  - [ ] `test` - Testing mode, special configs
  - [ ] Custom values documented

- [ ] **Security differences by environment**
  - [ ] Development: Stack traces in error responses
  - [ ] Production: Generic error messages only
  - [ ] Development: CORS wide open
  - [ ] Production: CORS restricted to domain
  - [ ] Development: Debug logging enabled
  - [ ] Production: Info/warn/error only

- [ ] **Template NODE_ENV usage**
  ```yaml
  NODE_ENV: "{{NODE_ENV}}"
  ```

### Security Scanning

- [ ] **Credential scanning**
  ```bash
  grep -r "password\|secret\|key\|token" . --include="*.js" --include="*.py" --include="*.yaml" | grep -v "example\|template\|TODO"
  grep -r "BEGIN.*PRIVATE\|BEGIN.*RSA" .  # Check for keys
  ```

- [ ] **Docker security**
  - [ ] No secrets in Dockerfile `ENV` instructions
  - [ ] Non-root user configured
  - [ ] Minimal base image (alpine, distroless)
  - [ ] No unnecessary packages installed
  - [ ] Secrets not in `docker inspect` output

- [ **TLS/SSL configuration**
  - [ ] HTTPS in production
  - [ ] Certificate paths parameterized
  - [ ] SSL validation enabled (not `--insecure`)
  - [ ] Certificate expiration monitoring

- [ ] **Network security**
  - [ ] Firewall rules documented
  - [ ] Internal services not Internet-exposed
  - [ ] API rate limiting configured
  - [ ] DDoS protection considered

- **Dependency vulnerabilities**
  - [ ] Dependencies scanned (npm audit, pip check)
  - [ ] Vulnerable packages documented or fixed
  - [ ] Regular update schedule defined
  - [ ] Software bill of materials (SBOM) generated

---

## Dependencies Checklist

### Runtime Dependencies

- [ ] **Identify all runtime dependencies**
  - [ ] Database (postgres, mysql, mongodb)
  - [ ] Cache (redis, memcached)
  - [ ] Message queue (rabbitmq, kafka, sqs)
  - [ ] Search (elasticsearch, typesense)
  - [ ] Storage (s3, gcs, azure storage)
  - [ ] External APIs (payment, auth, notification)

- [ ] **For each dependency:**
  - [ ] Required vs optional classification
  - [ ] Version compatibility matrix
  - [ ] Connection configuration
  - [ ] Health check mechanism
  - [ ] Failure impact analysis

### Service Dependencies

- [ ] **Internal services**
  - [ ] Authentication service
  - [ ] User management service
  - [ ] Notification service
  - [ ] Payment service
  - [ ] Logging/metrics service

- [ ] **Dependency discovery**
  - [ ] API calls to external services identified
  - [ ] Event publishing/subscription documented
  - [ ] Shared database access patterns
  - [ ] Cache dependencies identified

### Startup Order

- [ ] **Infrastructure first**
  1. Database (postgres/mysql)
  2. Cache (redis)
  3. Message queue (rabbitmq)
  4. Search (elasticsearch)

- [ ] **Application services**
  1. Core services (auth, user management)
  2. Business services (orders, payments)
  3. API gateway
  4. Frontend

- [ ] **Dependency configuration**
  ```yaml
  depends_on:
    postgres:
      condition: service_healthy  # Wait for DB ready
    redis:
      condition: service_started    # Just wait for start
  ```

### Version Constraints

- [ ] **Language version**
  - [ ] Python: `3.9`, `3.10`, `3.11` (specific, not `3`)
  - [ ] Node.js: `18`, `20` (LTS versions only)
  - [ ] Go: `1.20`, `1.21` (specific version)
  - [ ] Rust: edition and version pinned

- [ ] **Base image versions**
  - [ ] `python:3.11-slim` not `python:latest`
  - [ ] `node:20-alpine` not `node:alpine`
  - [ ] `golang:1.21-alpine` not `golang:alpine`
  - [ ] SHA256 digest pinning for immutability

---

## Testing Checklist

### Local Development Testing

- [ ] **Environment setup test**
  - [ ] Fresh clone builds successfully
  - [ ] `docker-compose up` starts all services
  - [ ] Application connects to dependencies
  - [ ] Health endpoints return 200

- [ ] **Configuration tests**
  - [ ] All environment variables recognized
  - [ ] Missing required variables fail clearly
  - [ ] Invalid values rejected with helpful errors
  - [ ] Defaults work when optional vars not set

### Integration Testing

- [ ] **Dependency connectivity**
  - [ ] Can connect to database
  - [ ] Can connect to cache
  - [ ] Can connect to message queue
  - [ ] Can call internal services

- [ ] **Failure scenarios**
  - [ ] Database down: app handles gracefully
  - [ ] Cache down: app continues (if optional)
  - [ ] Service down: circuit breaker opens
  - [ ] Network latency: timeouts trigger appropriately

### Production Readiness

- [ ] **Security validation**
  - [ ] No secrets in codebase (full git history scan)
  - [ ] Non-root user in container
  - [ ] Minimal attack surface
  - [ ] Security headers configured

- [ ] **Observability**
  - [ ] Logs written to stdout/stderr
  - [ ] Structured logging format
  - [ ] Metrics exposed (if applicable)
  - [ ] Health check endpoints work

- [ ] **Scalability**
  - [ ] Stateless application (can scale horizontally)
  - [ ] Database connection pooling configured
  - [ ] Cache externalized
  - [ ] No local file storage (or documented)

---

## Sign-off

**Skill Creator:** _______________________ Date: ____________

**Reviewed By:** _________________________ Date: ____________

**All Checklist Items Completed:** ☐ Yes ☐ No

**Items Not Applicable (N/A):** _________________________________________

**Additional Notes:**
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________
