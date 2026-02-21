# Gotchas and Known Issues

This document captures common failures, Docker vs Local mismatches, production-only bugs, and auth/CORS breakage examples. Learn from these to avoid repeating mistakes.

---

## Environment Variable Issues

### 1. Build-Time vs Runtime Confusion

**Problem:** Variables set during Docker build are not available at runtime.

**Example:**
```dockerfile
# WRONG - Will not be available at runtime
ARG DATABASE_URL="postgres://localhost/db"
RUN npm run build  # Build process uses this

# At runtime, DATABASE_URL is undefined!
```

**Solution:**
```dockerfile
# CORRECT - Set at runtime
ENV DATABASE_PASSWORD=""  # Placeholder
# Set real value when running:
# docker run -e DATABASE_URL="postgres://..." myapp
```

**Impact:** Application crashes with "undefined variable" error.

**How to Detect:**
```bash
# Check what's baked into image
docker inspect <image> --format='{{.Config.Env}}'

# Check what's actually set at runtime
docker run --rm <image> env
```

---

### 2. Environment Variable Naming Collisions

**Problem:** Using common variable names that conflict with system or other services.

**Example:**
```bash
# WRONG - Collides with system USER
USER=admin  # System uses $USER for current username

# WRONG - Collides with shell PATH
PATH=/custom/path  # Breaks all command execution
```

**Common Collision Names:**
- `HOME` - User home directory
- `PATH` - Command search path
- `USER` - Current username
- `HOSTNAME` - System hostname
- `PWD` - Current working directory

**Solution:**
```bash
# Prefix with APP_ or SERVICE_
APP_USER=admin
APP_PATH=/custom/path
```

---

### 3. Default Values in Production

**Problem:** Forgetting to set critical variables in production uses development defaults.

**Example:**
```javascript
// Default to development
db.connect({
  host: process.env.DATABASE_HOST || 'localhost',
  ssl: process.env.DB_SSL || false  // OOPS! No SSL in prod!
});
```

**How to Detect:**
```bash
# Check running container's env
docker exec <container> env | grep DATABASE

# Should NOT see:
DATABASE_HOST=localhost  # Wrong!
NODE_ENV=development     # Wrong!
```

**Prevention:**
```javascript
// Fail fast pattern - don't use defaults for prod
if (!process.env.DATABASE_HOST) {
  throw new Error('DATABASE_HOST is required');
}

if (process.env.NODE_ENV === 'production' && !process.env.DB_SSL) {
  throw new Error('DB_SSL must be true in production');
}
```

---

## Network & Connectivity Issues

### 4. Localhost in Containerized Apps (Classic!)

**Problem:** Service runs fine locally, fails in Docker because it tries to connect to itself instead of other container.

**Symptoms:**
```
Error: connect ECONNREFUSED 127.0.0.1:5432
    at TCPConnectWrap.afterConnect [as oncomplete]
```

**Root Cause:**
```javascript
// In docker-compose.yml, service config:
const db = new Client({
  host: 'localhost',  // Points to web container, not postgres!
  port: 5432
});
```

**Solution:**
```javascript
// Use service name from docker-compose.yml
const db = new Client({
  host: process.env.DATABASE_HOST || 'localhost',
  port: process.env.DATABASE_PORT || 5432
});
```

**Environment-specific values:**
```yaml
# Local: .env file
DATABASE_HOST=localhost

# Docker: docker-compose.yml environment
DATABASE_HOST=postgres-service

# Kubernetes: ConfigMap
DATABASE_HOST: postgres-service
```

**How to Debug:**
```bash
# Check connectivity from container
docker exec -it web_container sh
> nc -vz postgres-service 5432  # Should say "open"
> nc -vz localhost 5432         # Will say "connection refused"
```

---

### 5. Port Conflicts on Host Machine

**Problem:** Services can't start because default ports already in use.

**Common Conflicts:**
```
Port 3000 - Node.js default (used by many dev tools)
Port 5432 - PostgreSQL (if installed locally)
Port 6379 - Redis (if installed locally)
Port 8000 - Python/Django default
Port 8080 - Tomcat/Proxy servers
Port 5000 - Flask/macOS AirPlay
```

**Symptoms:**
```
Error starting userland proxy: listen tcp 0.0.0.0:5432:
bind: address already in use
```

**Solution:**
```yaml
# Parameterize host port, use alternative
services:
  web:
    ports:
      - "${WEB_HOST_PORT}:3000"  # Default to 3000
  postgres:
    ports:
      - "${DB_HOST_PORT}:5432"   # Default to 5432
```

```bash
# When ports are in use
WEB_HOST_PORT=3001 DB_HOST_PORT=5433 docker-compose up
```

**Impact Analysis Template:**
```yaml
EXPOSED_PORTS:
  - name: web
    internal: 3000
    external: "{{WEB_PORT}}"  # 3000 locally, 80 in prod
    protocol: TCP
    purpose: HTTP API
    security: public

  - name: database
    internal: 5432
    external: "{{DB_PORT}}"  # 5432 locally, not exposed in prod
    protocol: TCP
    purpose: PostgreSQL
    security: internal
```

---

### 6. Race Conditions in Startup Order

**Problem:** Application starts before database is ready.

**Symptoms:**
```
API server starting...
Error: connect ECONNREFUSED 172.18.0.2:5432
    at TCPConnectWrap.afterConnect
Crashed, restarting...
```

**Root Cause:**
```yaml
# docker-compose.yml - No dependency ordering
services:
  web:
    # No depends_on means web can start first
  postgres:
    # Database takes 5-10 seconds to initialize
```

**Why `depends_on` Alone Isn't Enough:**
```yaml
# This only waits for container to start, not for DB to be ready
depends_on:
  - postgres  # Container running ≠ DB ready
```

**Solutions:**

**Option 1: Health Checks with depends_on**
```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    depends_on:
      postgres:
        condition: service_healthy  # Waits for health check
```

**Option 2: Application-Level Retry**
```javascript
async function connectToDatabase() {
  let attempts = 0;
  while (attempts < 10) {
    try {
      await db.connect();
      console.log('Database connected');
      return;
    } catch (err) {
      attempts++;
      console.log(`DB connection failed, retry ${attempts}/10...`);
      await sleep(5000);  // Wait 5 seconds
    }
  }
  throw new Error('Could not connect to database');
}
```

**Option 3: Wrapper Script**
```bash
#!/bin/sh
# wait-for-postgres.sh
until pg_isready -h postgres-service -p 5432; do
  echo "Waiting for postgres..."
  sleep 2
done

exec "$@"
```

```yaml
# docker-compose.yml
command: ["./wait-for-postgres.sh", "npm", "start"]
```

---

## Auth & CORS Issues

### 7. Callback URL Mismatches in OAuth

**Problem:** OAuth login fails with "redirect_uri_mismatch" error.

**Why It Happens:**
```
Google OAuth Console configured callback:
https://myapp.com/auth/callback

Actual callback URL being used:
http://localhost:3000/auth/callback  (local dev)
```

**Environment Differences:**
```
Local:        http://localhost:3000/auth/callback
Docker:       http://localhost:3000/auth/callback
Staging:      https://staging.myapp.com/auth/callback
Production:   https://myapp.com/auth/callback
```

**Solution:**
```javascript
// Parameterize callback URL
const callbackURL = process.env.OAUTH_CALLBACK_URL ||
  `${process.env.BASE_URL}/auth/callback`;

passport.use(new GoogleStrategy({
  clientID: process.env.GOOGLE_CLIENT_ID,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET,
  callbackURL: callbackURL
}, ...));
```

```yaml
# Environment-specific values
# .env (local)
BASE_URL=http://localhost:3000

# docker-compose.yml (docker)
BASE_URL=http://localhost:3000

# production (K8s/Env)
BASE_URL=https://myapp.com
```

**Registration Process:**
```
For each environment, register callback URL:
1. Local: Add http://localhost:3000/auth/callback to OAuth provider
2. Staging: Add https://staging.myapp.com/auth/callback
3. Production: Add https://myapp.com/auth/callback

Use separate OAuth clients for each environment!
```

---

### 8. CORS Issues in Docker Environment

**Problem:** Frontend can't call API in Docker, getting CORS errors.

**Symptoms:**
```javascript
// Browser console
Access to fetch at 'http://localhost:3000/api/data' from origin
'http://localhost:3001' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested
resource.
```

**Why It Happens:**
```javascript
// Backend CORS config
app.use(cors({
  origin: 'http://localhost:3000'  // Only allows this exact origin
}));

// But frontend might be at:
// - http://localhost:3001 (different port)
// - https://app.localhost (different protocol)
// - https://staging.myapp.com (different domain)
```

**Environment Differences:**
```
Frontend Origins:
- Local: http://localhost:3000
- Docker: http://localhost:3000 or http://frontend:3000
- Staging: https://staging.myapp.com
- Production: https://myapp.com
```

**Solution:**
```javascript
// Option 1: Parameterized origin
const allowedOrigins = process.env.CORS_ORIGINS
  ? process.env.CORS_ORIGINS.split(',')
  : ['http://localhost:3000'];

app.use(cors({
  origin: allowedOrigins,
  credentials: true
}));
```

```yaml
# Environment configuration
# .env
CORS_ORIGINS=http://localhost:3000

# docker-compose.yml
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# production
CORS_ORIGINS=https://myapp.com
```

**Common CORS Gotchas:**

1. **Wildcards with Credentials**
```javascript
// WRONG - Wildcard + credentials = browser rejects
app.use(cors({
  origin: '*',
  credentials: true
}));

// CORRECT - Explicit origins with credentials
app.use(cors({
  origin: ['http://localhost:3000', 'https://myapp.com'],
  credentials: true
}));
```

2. **OPTIONS Preflight Requests**
```javascript
// Must handle OPTIONS requests
app.options('*', cors());  // Pre-flight requests
```

3. **Whitelisted Headers**
```javascript
// Must whitelist Authorization header
app.use(cors({
  exposedHeaders: ['Authorization']
}));
```

---

### 9. Session/Cookie Issues Across Environments

**Problem:** User logged in on localhost but not on production (or vice versa).

**Why It Happens:** Session secret is different:
```javascript
// Local .env
SESSION_SECRET=dev-secret-key

// Production
SESSION_SECRET=prod-secret-key  # Different!
```

Session cookie is encrypted with secret:
```javascript
Cookie: session=encrypted_with_dev_secret
// When sent to production, can't decrypt with prod secret
```

**Impact:** Sessions don't persist across environments (expected), but also causes:
- Session fixation attacks if secrets weak
- Session hijacking if secrets exposed
- Invalid sessions after deployment

**Solution:**
```javascript
// Strong, unique secret per environment
app.use(session({
  secret: process.env.SESSION_SECRET,  // Different per env
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',  // HTTPS only in prod
    httpOnly: true,
    sameSite: 'strict'
  }
}));
```

**Session Secret Requirements:**
- Randomly generated (32+ characters)
- Unique per environment
- Never committed to repository
- Rotated periodically
- Strong entropy (use `openssl rand -hex 32`)

---

## Docker-Specific Issues

### 10. Node Modules Volume Mounting

**Problem:** Works inside container, but can't find modules on host for IDE.

**Symptoms:**
```javascript
// VS Code shows red squiggles
import express from 'express';  // Error: Cannot find module 'express'
```

**Why It Happens:**
```yaml
# docker-compose.yml
volumes:
  - .:/app  # Mounts entire host directory

# But node_modules is in container, not on host!
```

**Solution:**
```yaml
# Use anonymous volume for node_modules
volumes:
  - .:/app
  - /app/node_modules  # Anonymous volume - preserves container's node_modules
```

**Alternative:**
```yaml
# Install dependencies on host first (workaround)
volumes:
  - .:/app

# Run on host: npm install
# Now node_modules exists on both host and container
```

---

### 11. File Watching Not Working in Docker

**Problem:** Hot reload doesn't work when files change.

**Why It Happens:**
```dockerfile
# Dockerfile
WORKDIR /app
COPY . .
RUN npm install

# docker-compose.yml
volumes:
  - .:/app  # Overwrites /app with host files
# But file system events don't propagate properly
```

**Symptoms:**
```bash
# Server started
[nodemon] starting `node server.js`

# File changed on host
[File] src/app.js modified

# But nodemon doesn't restart!
```

**Solution:**

**Option 1: Use polling**
```json
// nodemon.json or package.json
{
  "watch": ["src"],
  "ext": "js",
  "legacyWatch": true  // Use polling instead of fs events
}
```

**Option 2: Volume consistency**
```yaml
# docker-compose.yml (Docker Desktop for Mac/Windows)
volumes:
  - .:/app:consistent  # Ensures consistency
```

**Option 3: Use bind mount with inotify**
```yaml
# For Linux
volumes:
  - type: bind
    source: .
    target: /app
    bind:
      propagation: rslave
```

---

### 12. Database Files Permissions

**Problem:** Database can't write files, errors about permissions.

**Symptoms:**
```
PostgreSQL:
  FATAL: data directory "/var/lib/postgresql/data" has wrong ownership
  HINT: The server must be started by the user that owns the data directory

MySQL:
  mysqld: Can't create/write to file '/var/lib/mysql/ibdata1'

MongoDB:
  Unable to create/open lock file: /data/db/mongod.lock
  errno:13 Permission denied
```

**Why It Happens:**
```yaml
# docker-compose.yml
services:
  postgres:
    volumes:
      - ./data:/var/lib/postgresql/data
    # Container runs as postgres user (uid 999)
    # But ./data is owned by host user (uid 1000)
```

**Solution:**

**Option 1: Use named volumes**
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data  # Managed by Docker

volumes:
  postgres_data:  # No host ownership issues
```

**Option 2: Set user in Compose**
```yaml
# Run container as current host user
services:
  postgres:
    user: "${UID}:${GID}"  # Pass from host
```

**Option 3: Fix permissions**
```bash
# On host
mkdir -p data
sudo chown -R 999:999 data  # Match container user's UID
```

---

## Production-Only Issues

### 13. Different Behavior in Production vs Staging

**Problem:** Staging works, production fails, identical code.

**Common Causes:**

**1. Different Environment Variables**
```yaml
# Staging
LOG_LEVEL=debug  # Shows debug info

# Production
LOG_LEVEL=info   # Less verbose, hides issues
```

**Impact:** Errors hidden in production logs.

**2. Different Database Versions**
```yaml
# Staging docker-compose.yml
postgres:12-alpine

# Production RDS
PostgreSQL 14.5  # Newer version!
```

**Impact:** Queries work in staging, fail in production.

**3. Different Scale**
```yaml
# Staging
1 web server
1 database (small)

# Production
5 web servers
1 database (large)
```

**Impact:**
- Database connection pool exhaustion
- Lock contention
- Race conditions only at scale

**Prevention:**
- Infrastructure as Code (same setup everywhere)
- Staging mirrors production
- Load testing before prod deploy
- Environment variable parity audit

---

### 14. Connection Pool Exhaustion

**Problem:** Works with few users, crashes under load.

**Symptoms:**
```
Error: Pool is closed
Error: Sorry, too many clients already
Error: Connection terminated due to connection timeout
```

**Why It Happens:**
```javascript
// Default connection pool too small
const pool = new Pool({
  max: 10,  // Default, too low for production
});

// With 5 app servers × 10 connections = 50 max
// But PostgreSQL default max_connections = 100
// Leaves only 50 for other services/replicas
```

**Solution:**
```javascript
// Calculate proper pool size
const maxConnections = 100;  // PostgreSQL max_connections
const appInstances = 5;      // Number of app replicas
const overhead = 10;         // Leave for admin/monitoring

const poolSize = Math.floor((maxConnections - overhead) / appInstances);
// (100 - 10) / 5 = 18 connections per app

const pool = new Pool({
  max: poolSize,
  min: 5,  // Keep some connections warm
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});
```

**Configuration:**
```yaml
# environment variables
DB_POOL_MAX={{DATABASE_POOL_MAX}}  # Calculate per environment
DB_POOL_MIN={{DATABASE_POOL_MIN}}
DB_IDLE_TIMEOUT={{DATABASE_IDLE_TIMEOUT}}
```

---

### 15. Timezone Issues in Production

**Problem:** Timestamps are wrong by hours in production.

**Why It Happens:**
```javascript
// Database stores UTC
2023-10-01 14:00:00 UTC

// App server runs in UTC (Docker default)
// Displays as: 2:00 PM (correct)

// App server runs in EST (local dev)
// Displays as: 10:00 AM (wrong!)
```

**Solution:**

**1. Use UTC in database**
```sql
-- PostgreSQL
CREATE TABLE events (
  happened_at TIMESTAMPTZ  -- With timezone
);

-- Always store UTC
INSERT INTO events (happened_at) VALUES (NOW() AT TIME ZONE 'UTC');
```

**2. Configure application timezone**
```javascript
// Node.js
process.env.TZ = 'UTC';  // Force UTC

// Or in Dockerfile
ENV TZ=UTC
```

**3. Display in user's timezone**
```javascript
// Store UTC, convert on display
const utcTime = new Date('2023-10-01T14:00:00Z');
const localTime = utcTime.toLocaleString('en-US', {
  timeZone: user.timezone  // 'America/New_York'
});
```

**4. Environment variable**
```yaml
TZ: {{TZ}}  # UTC in production, can be local in dev
```

---

## Kubernetes-Specific Issues

### 16. ConfigMap vs Secret Confusion

**Problem:** Sensitive data in ConfigMap (visible to everyone), or non-sensitive data in Secret (unnecessary overhead).

**Wrong:**
```yaml
# ConfigMap with sensitive data!
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database-password: "secret123"  # VISIBLE TO ALL!
```

**Also Wrong:**
```yaml
# Secret with non-sensitive data (overkill)
apiVersion: v1
kind: Secret
metadata:
  name: app-config
type: Opaque
data:
  app-name: bXktYXBw  # base64 of "my-app" (not sensitive!)
```

**Correct:**
```yaml
# ConfigMap - non-sensitive configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  app-name: "my-app"
  log-level: "info"
  database-host: "postgres-service"

---
# Secret - sensitive data only
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  database-password: c2VjcmV0MTIz  # base64 encoded
```

**Rule of Thumb:**
- ConfigMap: Configuration, feature flags, endpoints, ports
- Secret: Passwords, API keys, certificates, tokens

---

### 17. Liveness vs Readiness Probe Misconfiguration

**Problem:** Pod keeps restarting even though it's working, or traffic sent to pod before it's ready.

**Wrong (liveness = readiness):**
```yaml
# Liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 5

# Readiness probe (same as liveness!)
readinessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 5
```

**Result:**
- App starts up, takes 20 seconds to be ready
- Liveness probe fails at 10 seconds (not ready yet!)
- Kubernetes kills pod and restarts
- Infinite restart loop!

**Correct:**
```yaml
# Readiness - is app ready to receive traffic?
readinessProbe:
  httpGet:
    path: /health/ready  # Checks DB, cache etc.
    port: 3000
  initialDelaySeconds: 10  # Wait 10s before checking
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 3  # Allow 3 failures before marking unready

# Liveness - is app still running?
livenessProbe:
  httpGet:
    path: /health/live  # Simple ping
    port: 3000
  initialDelaySeconds: 30  # Wait longer for liveness
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3
```

**Different endpoints:**
```javascript
// /health/live - Simple liveness check
app.get('/health/live', (req, res) => {
  res.status(200).send('OK');  // Always 200 if server running
});

// /health/ready - Readiness check
app.get('/health/ready', async (req, res) => {
  try {
    // Check all dependencies
    await db.query('SELECT 1');
    await cache.ping();
    res.status(200).send('Ready');
  } catch (err) {
    res.status(503).send('Not Ready');
  }
});
```

---

## Database Issues

### 18. Database Migrations in Production

**Problem:** New code deploys successfully but crashes because database schema not migrated.

**Why It Happens:**
```yaml
# CI/CD Pipeline
1. Deploy new container (v2.0)
2. Start application
3. Application expects 'users.email' column
4. Database still has old schema (v1.0)
5. CRASH: column "email" does not exist
```

**Solution:**

**Option 1: Migrate on Startup (simple)**
```javascript
// In app startup
async function startApp() {
  await runMigrations();  // Migrate first
  await app.listen(3000);  // Then start server
}
```

**Option 2: Init Containers (K8s)**
```yaml
apiVersion: v1
kind: Pod
spec:
  initContainers:
  - name: migrate
    image: myapp:v2.0
    command: ['npm', 'run', 'migrate']
  containers:
  - name: app
    image: myapp:v2.0
    command: ['npm', 'start']
```

**Option 3: Separate Migration Job**
```yaml
# Run migration before deployment
kubectl create job migration-job --image=myapp:v2.0 -- npm run migrate

# Wait for completion, then deploy
kubectl wait --for=condition=complete job/migration-job
kubectl apply -f deployment.yml
```

**Best Practice:**
- Migrations should be backward compatible
- New code should work with old schema (during rollout)
- New schema should work with old code (for rollback)
- Test migrations on staging with production-like data

---

### 19. Migration Rollback Issues

**Problem:** Need to rollback deploy, but database migration already ran and isn't reversible.

**Bad Migration:**
```sql
-- Can't rollback - column dropped permanently
ALTER TABLE users DROP COLUMN email;
```

**Good Migration:**
```sql
-- Reversible migration
-- forward: rename column
ALTER TABLE users RENAME COLUMN email TO user_email;

-- rollback: rename back
-- ALTER TABLE users RENAME COLUMN user_email TO email;
```

**Best Practice:**
```sql
-- Always make reversible migrations
-- 1. Add new column (backward compatible)
ALTER TABLE users ADD COLUMN email VARCHAR(255);

-- 2. Backfill data
UPDATE users SET email = old_email_column;

-- 3. Deploy code using new column
-- 4. Later: drop old column in separate migration
```

**Rollback Strategy:**
```bash
# If deploy fails after migration
1. Rollback application version (v2.0 → v1.0)
2. **Don't rollback migration!** Old code works with new schema
3. Fix forward (v2.1) and redeploy

# Only rollback migration if:
- Migration itself is broken
- Schema change is incompatible with old code
```

---

## Testing/Debugging Techniques

### Quick Environment Validation

**Check all environment variables:**
```bash
docker exec container env | sort | grep -v "PATH\|HOME\|PWD\|USER"
```

**Check connectivity:**
```bash
# From web container
docker exec -it web_container sh
> nc -vz postgres-service 5432
docker exec -it web_container sh
> nc -vz postgres-service 5432
Connection to postgres-service 5432 port [tcp/postgresql] succeeded!

> nc -vz redis-service 6379
Connection to redis-service 6379 port [tcp/*] succeeded!
```

**Check DNS resolution:**
```bash
docker exec -it web_container sh
> nslookup postgres-service
Name: postgres-service
Address: 172.18.0.2
```

**View logs from all services:**
```bash
docker-compose logs -f --tail=20
```

**Check container health:**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## Common Error Messages and Solutions

### "Connection refused"
```
Error: connect ECONNREFUSED 127.0.0.1:5432
- Cause: Using localhost in container
- Fix: Use service name

Error: connect ECONNREFUSED 172.18.0.3:5432
- Cause: Service not ready or crashed
- Fix: Check health, add retries
```

### "Connection timeout"
```
Error: connect ETIMEDOUT 172.18.0.3:5432
- Cause: Network issue or wrong host
- Fix: Check DNS, verify service exists
```

### "getaddrinfo ENOTFOUND"
```
Error: getaddrinfo ENOTFOUND postgres-service
- Cause: DNS can't resolve service name
- Fix: Check service name, verify same network
```

### "SSL/TLS errors"
```
Error: self signed certificate
- Cause: Using HTTPS with self-signed cert
- Fix: Use proper cert or disable SSL (dev only)

Error: unable to verify the first certificate
- Cause: Certificate chain incomplete
- Fix: Provide CA certificate
```

---

## Prevention Checklist

Before deploying to production:

- [ ] All `localhost` removed from code
- [ ] All secrets externalized
- [ ] All ports parameterized
- [ ] Health endpoints implemented
- [ ] Graceful degradation enabled
- [ ] Timeout and retry logic added
- [ ] Database migrations tested
- [ ] CORS origins configured
- [ ] OAuth callbacks registered
- [ ] Environment variables documented
- [ ] Service dependencies defined
- [ ] Startup ordering configured
- [ ] Log aggregation verified
- [ ] Metrics/monitoring enabled
- [ ] Rollback plan documented
- [ ] Database backups confirmed

---

## When to Consult This Document

**Before creating a skill:** Review relevant patterns
**During development:** Check gotchas for tech stack
**Before production:** Complete prevention checklist
**When debugging:** Search error messages above
**During code review:** Reference anti-patterns

---
