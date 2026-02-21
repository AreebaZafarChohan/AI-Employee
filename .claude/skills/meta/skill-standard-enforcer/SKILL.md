---
name: skill-standard-enforcer
description: Enforces a single canonical pattern for creating all Claude agent skills. This skill MUST be used whenever a new skill is created. It ensures blueprint-driven structure, impact analysis, references, assets, and validation checklists are always present.
---

# Skill Standard Enforcer

## Purpose

This is a **meta-skill** that governs how **all other skills** are created.

No skill is considered valid unless it follows the enforced pattern defined here.

This prevents:
- Fragile one-off skills
- Config-only skills with no context
- Deployment skills without impact analysis
- Skills that break when moving from local → Docker → Kubernetes

---

## When to Use This Skill

This skill MUST be invoked when:

- Creating **any new skill**
- Modifying an existing skill's structure
- Creating deployment, infra, CI/CD, auth, or automation skills
- Containerizing or orchestrating applications
- Generating templates (Docker, Helm, K8s, pipelines)

If this skill is NOT applied → the output should be rejected.

---

## Canonical Skill Pattern (MANDATORY)

Every skill MUST follow this structure:

```
.claude/skills/<domain>/<skill-name>/
├── SKILL.md
├── references/
│   ├── patterns.md
│   ├── impact-checklist.md
│   ├── gotchas.md
└── assets/
    ├── *.template
    ├── *.example
```

If any part is missing → skill is invalid.

---

## Required Sections in SKILL.md

Every SKILL.md MUST contain:

1. **Overview**
2. **When to Use This Skill**
3. **Impact Analysis Workflow**
4. **Environment Variable Strategy**
5. **Network & Topology Implications**
6. **Auth / CORS / Security Impact**
7. **Blueprints & Templates Used**
8. **Validation Checklist**
9. **Anti-Patterns**

---

## Impact Analysis Workflow

### 1. Environment Variable Strategy

Before any config or template is generated, the skill MUST:

**Build-Time vs Runtime Variables:**
- Identify all environment variables required by the service
- Separate BUILD_TIME variables (used during image build):
  - `BUILD_TARGET`
  - `BUILD_VERSION`
  - `BUILD_COMMIT_SHA`
- Separate RUNTIME variables (used when container runs):
  - `DATABASE_URL`
  - `API_KEY`
  - `LOG_LEVEL`

**Secrets Management:**
- Never hardcode secrets in templates or Dockerfiles
- Mark secret variables clearly: `{{SECRET_KEY}}` (sensitive)
- Always reference external secret stores:
  - `.env` file for local development
  - Docker secrets for Docker Swarm
  - Kubernetes secrets for K8s
  - Vault/Parameter Store for production

**Variable Discovery Process:**
```bash
# Search for environment variable usage
grep -r "process.env" src/
grep -r "\.env\|getenv" . --include="*.py" --include="*.js"
docker run --rm <image> env  # Check container's base env
```

### 2. Network & Topology Implications

**Port Discovery:**
- Identify all ports the service exposes
- Map HTTP ports (80, 8080, 3000, 8000, 5000)
- Map non-HTTP ports (databases, message queues)
- Document for each port:
  - Internal port (container listens on)
  - External port (host/service receives on)
  - Protocol (TCP, UDP)
  - Purpose (HTTP, HTTPS, gRPC, custom)

**localhost Detection & Correction:**
- Scan for `localhost` usage in configs:
  - `127.0.0.1`
  - `localhost`
  - `0.0.0.0`
- Map to service names:
  - `localhost:5432` → `{{DATABASE_HOST}}:5432`
  - `localhost:6379` → `{{CACHE_HOST}}:6379`
  - `localhost:9200` → `{{SEARCH_HOST}}:9200`

**Dependency Topology:**
- Document service dependencies in startup order:
  ```
  1. database (postgres/mysql) - required before app
  2. cache (redis) - optional, app can start without
  3. search (elasticsearch) - optional, degraded mode if down
  4. message queue (rabbitmq) - optional, async fallbacks
  ```

**Network Policy Considerations:**
- Ingress: Which services can call this service?
- Egress: Which services does this service call?
- Internal vs External: Is this service Internet-facing?
- Protocol: HTTP/2, WebSockets, gRPC? Special configuration needed?

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**
- Identify authentication mechanism:
  - JWT tokens (stateless)
  - Session cookies (stateful)
  - OAuth 2.0 / OpenID Connect (third-party)
  - API Keys (service-to-service)

**CORS Impact:**
- Document allowed origins per environment:
  - Local: `http://localhost:3000`
  - Docker: `http://localhost:3000`
  - Production: `https://{{APP_DOMAIN}}`
- Detect wildcard patterns: `*` (security risk)
- Configure proper origin lists in templates

**Callback URL Changes:**
When deploying to different environments, URLs change:
- Local: `http://localhost:8000/auth/callback`
- Docker Compose: `http://web:8000/auth/callback`
- K8s: `http://web-service:8000/auth/callback`
- Production: `https://{{APP_DOMAIN}}/auth/callback`

This impacts:
- OAuth callback URLs (must be registered with provider)
- Webhook endpoints
- Redirect URLs after authentication

**NODE_ENV Behavior:**
Different environments have different security profiles:
- `development`: Stack traces, debug mode, loose CORS
- `production`: HSTS, secure cookies, strict CSP, limited CORS

Template must include:
```yaml
NODE_ENV: "{{NODE_ENV}}"  # production | development
```

**Security Scanning Requirements:**
- Scan for hardcoded credentials: `grep -r "password\|secret\|key" . --include="*.env.example"`
- Scan for TLS/SSL configuration issues
- Check for exposed ports in Docker images
- Verify non-root user execution

---

## Blueprints & Templates Used

### Blueprint: Skill Structure Template

**Purpose:** Generate canonical skill directory structure

**When to Use:**
- Every new skill creation
- Retrofitting existing skills to meet standards

**When NOT to Use:**
- Temporary, one-off scripts
- Documentation-only skills with no operational impact

**Template Variables:**
```yaml
# Directory structure
DOMAIN: "meta"                                  # Domain classification
SKILL_NAME: "skill-standard-enforcer"          # Skill identifier

# SKILL.md sections
OVERVIEW: "brief description"
WHEN_TO_USE: "trigger conditions"
IMPACT_WORKFLOW: "analysis steps"
ENV_STRATEGY: "variable handling"
NETWORK_IMPLICATIONS: "ports and topology"
AUTH_IMPACT: "security considerations"
BLUEPRINTS_USED: "template references"
VALIDATION_CHECKLIST: "quality gates"
ANTI_PATTERNS: "what to avoid"

# References content
PATTERNS_DOC: "pattern documentation"
IMPACT_CHECKLIST_DOC: "environment checklists"
GOTCHAS_DOC: "known issues"
```

**Impact Notes:**
- This template creates **mandatory file structure**
- Missing any file renders skill invalid
- All placeholders must be replaced with actual content
- Templates must be parameterized, no hardcoded values

### Blueprint: Environment Variables Template

**Purpose:** Generate environment variable configuration

**When to Use:**
- Services requiring external configuration
- Multi-environment deployments
- Secret management integration

**When NOT to Use:**
- Hardcoded configuration works
- No environment-specific values needed
- Single environment deployment only

**Template Variables:**
```yaml
# Build-time variables
BUILD_TARGET: "production"
BUILD_VERSION: "{{GIT_COMMIT_SHA}}"
BUILD_TIMESTAMP: "{{CURRENT_TIMESTAMP}}"

# Runtime variables (non-secret)
APP_PORT: "{{PORT}}"
LOG_LEVEL: "{{LOG_LEVEL}}"
DATABASE_HOST: "{{DB_SERVICE_NAME}}"
DATABASE_PORT: "{{DB_PORT}}"

# Runtime variables (secrets - external management)
# These should NOT have default values in templates
DATABASE_PASSWORD: "{{SECRET_DATABASE_PASSWORD}}"
API_KEY: "{{SECRET_API_KEY}}"
JWT_SECRET: "{{SECRET_JWT_SECRET}}"
```

**Impact Notes:**
- `{{SECRET_*}}` variables **must not** have default values
- Passwords in `.env.example` should be placeholders like `change_me`
- Different environments need different variable sets
- Docker Compose vs K8s secret mounting differs

### Blueprint: Docker Compose Template

**Purpose:** Generate multi-service development environment

**When to Use:**
- Local development with multiple services
- Integration testing
- Pre-production validation

**When NOT to Use:**
- Single service with no dependencies
- Production deployments (use K8s instead)

**Template Variables:**
```yaml
version: '3.8'
services:
  {{SERVICE_NAME}}:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - BUILD_TARGET={{BUILD_TARGET}}
    ports:
      - "{{HOST_PORT}}:{{CONTAINER_PORT}}"
    environment:
      - NODE_ENV={{NODE_ENV}}
      - DATABASE_URL=postgres://{{DB_USER}}:{{DB_PASS}}@{{DB_SERVICE_NAME}}:{{DB_PORT}}/{{DB_NAME}}
      - CACHE_URL=redis://{{CACHE_SERVICE_NAME}}:{{CACHE_PORT}}
    depends_on:
      - {{DB_SERVICE_NAME}}
      - {{CACHE_SERVICE_NAME}}
    networks:
      - {{NETWORK_NAME}}

  {{DB_SERVICE_NAME}}:
    image: postgres:{{POSTGRES_VERSION}}
    environment:
      - POSTGRES_DB={{DB_NAME}}
      - POSTGRES_USER={{DB_USER}}
      - POSTGRES_PASSWORD={{DB_PASS}}
    volumes:
      - {{DB_VOLUME_NAME}}:/var/lib/postgresql/data
    networks:
      - {{NETWORK_NAME}}

  {{CACHE_SERVICE_NAME}}:
    image: redis:{{REDIS_VERSION}}
    networks:
      - {{NETWORK_NAME}}

networks:
  {{NETWORK_NAME}}:
    driver: bridge

volumes:
  {{DB_VOLUME_NAME}}:
```

**Impact Notes:**
- `depends_on` ensures proper startup order
- Service names replace `localhost` in URLs
- Database passwords should come from `.env` file, not hardcoded
- All services must share a network to communicate
- Port mapping (host:container) allows external access

### Blueprint: Database Connection Template

**Purpose:** Generate database connection configuration

**When to Use:**
- Services requiring database access
- Multiple database types (SQL, NoSQL)
- Connection pooling configuration

**Template Variables:**
```yaml
# Database connection string templates
POSTGRES_URL: "postgresql://{{DB_USER}}:{{DB_PASS}}@{{DB_HOST}}:{{DB_PORT}}/{{DB_NAME}}?sslmode={{DB_SSL_MODE}}"
MYSQL_URL: "mysql://{{DB_USER}}:{{DB_PASS}}@{{DB_HOST}}:{{DB_PORT}}/{{DB_NAME}}"
MONGODB_URL: "mongodb://{{DB_USER}}:{{DB_PASS}}@{{DB_HOST}}:{{DB_PORT}}/{{DB_NAME}}"

# Connection pool settings
DB_POOL_MIN: "{{DB_POOL_MIN}}"          # Minimum connections
DB_POOL_MAX: "{{DB_POOL_MAX}}"          # Maximum connections
DB_TIMEOUT: "{{DB_TIMEOUT_MS}}"       # Connection timeout (ms)
DB_IDLE_TIMEOUT: "{{DB_IDLE_TIMEOUT}}" # Idle connection timeout
```

**Impact Notes:**
- SSL mode differs per environment (disable locally, require in prod)
- Connection pooling prevents DB overload
- Timeout values should vary (longer locally, shorter in prod)
- Username/password **must not** be hardcoded

### Blueprint: CORS Configuration Template

**Purpose:** Generate CORS policy configuration

**When to Use:**
- Web APIs accessed from browsers
- Multi-domain applications
- Third-party frontend access

**When NOT to Use:**
- Service-to-service communication (internal)
- Non-HTTP protocols
- Same-origin only applications

**Template Variables:**
```yaml
# CORS configuration
CORS_ENABLED: "{{CORS_ENABLED}}"                      # true | false
CORS_ORIGIN: "{{CORS_ALLOWED_ORIGIN}}"                # Specific origin or comma-separated list
CORS_CREDENTIALS: "{{CORS_ALLOW_CREDENTIALS}}"       # true | false
CORS_METHODS: "GET,POST,PUT,DELETE,OPTIONS"          # HTTP methods allowed
CORS_HEADERS: "Content-Type,Authorization"            # Headers allowed
CORS_MAX_AGE: "{{CORS_MAX_AGE_SEC}}"                  # Preflight cache duration

# Environment-specific origins
DEV_ORIGIN: "http://localhost:3000"
STAGING_ORIGIN: "https://staging.{{APP_DOMAIN}}"
PROD_ORIGIN: "https://{{APP_DOMAIN}}"
```

**Impact Notes:**
- Wildcard `*` with credentials is a security vulnerability
- Origins **must** change per environment
- Credentials require explicit origin, not wildcard
- Max age reduces preflight requests
- Multiple origins require server-side validation loop

---

## Validation Checklist

### Mandatory Checks (Skill Invalid If Failed)

- [ ] Uses canonical folder structure: `SKILL.md`, `references/`, `assets/`
- [ ] Contains complete impact analysis (Env, Network, Auth)
- [ ] No `localhost` hardcoding in any template
- [ ] No secrets or passwords in templates or examples
- [ ] Auth/CORS impact explicitly documented
- [ ] Supports containerization (Docker) and orchestration (K8s)
- [ ] Gotchas document has known failures and mitigation
- [ ] Anti-patterns list common mistakes
- [ ] All templates use parameterized placeholders `{{VARIABLE}}`
- [ ] Templates include IMPACT NOTES comments
- [ ] References folder has all three files (patterns, impact-checklist, gotchas)
- [ ] SKILL.md contains all 9 required sections

### Quality Checks (Skill Degraded If Failed)

- [ ] Default values only for non-sensitive variables
- [ ] `.example` files show realistic placeholder values
- [ ] Variable naming follows consistent pattern
- [ ] Ports documented (internal vs external)
- [ ] Dependencies have startup order documented
- [ ] Health check endpoints identified
- [ ] Graceful degradation scenarios outlined

### Environment Readiness Checks

- [ ] Variables compatible with:
  - [ ] Local development (`.env` files)
  - [ ] Docker Compose
  - [ ] Kubernetes (using ConfigMaps/Secrets)
- [ ] Network configuration works in:
  - [ ] Docker bridge networks
  - [ ] Docker Compose service discovery
  - [ ] Kubernetes service mesh
- [ ] Auth configuration handles:
  - [ ] Callback URL changes per environment
  - [ ] CORS origin changes per environment
  - [ ] Different OAuth providers per environment

---

## Anti-Patterns

### ❌ Hardcoding `localhost`

**Problem:** Service fails when containerized

**Example:**
```javascript
// WRONG
const db = new Client({ host: 'localhost' });

// CORRECT
const db = new Client({ host: process.env.DATABASE_HOST || 'localhost' });
```

### ❌ Secrets in Docker Images

**Problem:** Credentials baked into image, security vulnerability

**Example:**
```dockerfile
# WRONG
ENV DATABASE_PASSWORD="actual_password_here"
ENV API_KEY="sk_live_actual_key"

# CORRECT
ENV DATABASE_PASSWORD=""
ENV API_KEY=""
# Set at runtime via docker run -e or orchestrator
```

### ❌ Fixed Ports in Templates

**Problem:** Port conflicts in multi-service deployments

**Example:**
```yaml
# WRONG
ports:
  - "3000:3000"  # Fixed, will conflict

# CORRECT
ports:
  - "{{HOST_PORT}}:{{CONTAINER_PORT}}"  # Parameterized
```

### ❌ No Health Checks

**Problem:** Orchestrator cannot determine service health

**Example:**
```dockerfile
# WRONG
# No HEALTHCHECK instruction

# CORRECT
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:{{PORT}}/health || exit 1
```

### ❌ No Dependency Awareness

**Problem:** Application starts before database ready

**Example:**
```yaml
# WRONG
services:
  web:
    depends_on: []  # No dependency declared

# CORRECT
services:
  web:
    depends_on:
      - database
    restart: unless-stopped
```

### ❌ No Environment Differentiation

**Problem:** Production runs with development settings

**Example:**
```bash
# WRONG
NODE_ENV=development  # Same for all environments

# CORRECT
# Local: NODE_ENV=development
# Docker: NODE_ENV=production (even for local Docker)
# K8s/Prod: NODE_ENV=production
```

### ❌ Inconsistent Variable Naming

**Problem:** Confusion between similar variables

**Example:**
```yaml
# WRONG
DATABASE_URL=...
DB_CONNECTION=...  # Same thing, different name

# CORRECT
DATABASE_URL=...  # Single source of truth
```

### ❌ Missing Error Handling

**Problem:** Service crashes on transient failures

**Example:**
```javascript
// WRONG
try {
  await db.connect();
} catch (err) {
  console.error(err);  // Just log, still crash
  process.exit(1);
}

// CORRECT
try {
  await db.connect();
} catch (err) {
  console.error('DB connection failed, retrying in 5s...', err);
  setTimeout(connectWithRetry, 5000);  // Retry logic
}
```

### ❌ No Graceful Degradation

**Problem:** Entire app crashes if optional service down

**Example:**
```javascript
// WRONG - Cache is optional, but app crashes without it
const cache = await connectToRedis();
if (!cache) {
  throw new Error('Cache required');  // Should not crash
}

// CORRECT
let cache = null;
try {
  cache = await connectToRedis();
} catch (err) {
  console.warn('Cache unavailable, operating without cache');
}
```

### ❌ Lack of Observability

**Problem:** Cannot debug production issues

**Example:**
```yaml
# WRONG - No log configuration
environment: []

# CORRECT
environment:
  - LOG_LEVEL={{LOG_LEVEL}}  # debug | info | warn | error
  - LOG_FORMAT=json  # Structured logging
  - ENABLE_METRICS=true
```

---

## Enforcement Behavior

When this skill is active:

### Claude's Responsibilities

1. **Refuse Non-Compliant Skills**
   - If skill structure doesn't match canonical pattern → reject creation
   - If impact analysis missing → request completion before proceeding
   - If templates hardcode values → require parameterization

2. **Suggest Missing Sections**
   - Identify which required sections are missing
   - Explain why each section is critical
   - Provide examples of proper content

3. **Explain Validation Failures**
   - Reference specific checklist items that failed
   - Show examples of correct vs incorrect patterns
   - Explain production impact of the issue

4. **Regenerate Skill Scaffolding**
   - If skill is rejected, regenerate entire structure
   - Preserve any valid content that exists
   - Fill in missing sections with proper templates

### User Expectations

- All skill creation requests will be validated against this standard
- The skill-standard-enforcer runs automatically for every new skill
- Non-compliant skills will not be created
- Clear explanations provided for all rejections

---

## Final Rule (Hard Stop)

If a user asks to create a skill **without** requiring this pattern:

```
User: "Just give me a simple Dockerfile, skip the rest"

Claude: "This request violates the enforced skill standard.

I cannot create a Dockerfile without:
- Impact analysis (ENV, Network, Auth)
- Parameterization
- Environment compatibility
- Security review

I will generate a blueprint-driven, impact-aware skill structure that includes
the Dockerfile you need, properly configured for all environments."
```

Then proceed to create the full skill structure using this standard.

---
