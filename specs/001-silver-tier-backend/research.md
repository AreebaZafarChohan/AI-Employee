# Research & Technology Decisions: Silver Tier Backend

**Date**: 2026-02-22
**Feature**: Silver Tier Backend
**Branch**: 001-silver-tier-backend

## Technology Decisions

### Decision 1: Web Framework Selection

**What was chosen**: Express.js

**Why chosen**:
- Mature ecosystem with extensive middleware support
- Simpler learning curve for rapid Silver-tier development
- Sufficient performance for Silver-tier requirements (single instance, no high-concurrency demands)
- Better documentation and community support for common patterns
- Compatible with all required dependencies (Prisma, Zod)

**Alternatives considered**:
- **Fastify**: Faster performance but steeper learning curve; performance benefits not critical for Silver tier
- **Koa**: More modern but smaller ecosystem; less direct TypeScript support
- **NestJS**: Over-engineered for Silver-tier scope; adds unnecessary complexity

---

### Decision 2: Database Schema Design Pattern

**What was chosen**: Prisma ORM with explicit schema design

**Why chosen**:
- Type-safe database operations out of the box
- Automatic migration generation
- Excellent TypeScript integration
- Clear schema definition language
- Active development and community support

**Alternatives considered**:
- **TypeORM**: More complex, less intuitive API
- **Knex.js**: Lower-level, requires more boilerplate
- **Raw SQL**: Loses type safety, more error-prone

---

### Decision 3: Validation Strategy

**What was chosen**: Zod schema validation

**Why chosen**:
- Runtime type validation with TypeScript inference
- Single source of truth for types
- Excellent error messages
- Composable schemas
- Growing adoption and maintenance

**Alternatives considered**:
- **Joi**: Mature but doesn't infer TypeScript types
- **Yup**: Similar to Zod but less TypeScript-focused
- **class-validator**: Requires decorators, more boilerplate

---

### Decision 4: Testing Framework

**What was chosen**: Jest + Supertest

**Why chosen**:
- Jest: Industry standard for Node.js testing
- Built-in mocking and snapshot testing
- Excellent TypeScript support
- Supertest: Simple HTTP assertion library for API testing
- Works seamlessly with Express

**Alternatives considered**:
- **Vitest**: Faster but less mature ecosystem
- **Mocha/Chai**: More configuration required, older patterns
- **node:test**: Built-in but less feature-rich than Jest

---

### Decision 5: AI Provider Abstraction Pattern

**What was chosen**: Strategy pattern with factory

**Why chosen**:
- Clean separation of concerns
- Easy to swap providers via environment variable
- Testable with mock providers
- Extensible for future providers
- No direct AI calls in business logic

**Implementation**:
```typescript
interface AIProvider {
  generatePlan(task: Task): Promise<PlanStep[]>;
}

function createAIProvider(providerType: string): AIProvider {
  // Returns appropriate provider based on env config
}
```

**Alternatives considered**:
- **Direct integration**: Simpler but violates separation of concerns
- **Adapter pattern**: Over-engineered for single-provider-at-a-time requirement
- **Event-driven**: Unnecessary complexity for Silver tier

---

### Decision 6: Project Structure Pattern

**What was chosen**: Service-layer architecture

**Why chosen**:
- Clear separation: Controllers → Services → Models
- Testable at each layer
- Standard pattern for REST APIs
- Scales well for Silver → Gold evolution
- Enforces single responsibility principle

**Layer responsibilities**:
- **Controllers**: HTTP request/response handling, validation
- **Services**: Business logic, domain rules, state transitions
- **Models**: Database operations, type definitions

**Alternatives considered**:
- **MVC**: Less explicit service layer, can lead to fat controllers
- **Clean Architecture**: Over-engineered for Silver tier
- **Monolithic**: Harder to test and maintain

---

### Decision 7: Docker Configuration Strategy

**What was chosen**: Multi-stage Docker build

**Why chosen**:
- Smaller production image (no dev dependencies)
- Reproducible builds
- Environment-based configuration
- Docker Compose for local development with PostgreSQL

**Configuration approach**:
- Development: `docker-compose.yml` with PostgreSQL service
- Production: Single-container build with external database
- Environment variables for all configuration

**Alternatives considered**:
- **Single-stage build**: Simpler but larger image
- **Helm charts**: Over-engineered for Silver tier
- **Docker Swarm**: Unnecessary; single instance deployment

---

### Decision 8: Error Handling Strategy

**What was chosen**: Centralized error middleware with custom error classes

**Why chosen**:
- Consistent error responses across all endpoints
- Separation of error types (validation, not found, server)
- No internal details leaked to clients
- Easy to extend for new error types

**Error hierarchy**:
```typescript
class AppError extends Error {
  statusCode: number;
  isOperational: boolean;
}

class ValidationError extends AppError { }
class NotFoundError extends AppError { }
class ServiceUnavailableError extends AppError { }
```

**Alternatives considered**:
- **Try-catch in each controller**: Repetitive, error-prone
- **Express error handling only**: Less type safety
- **Domain-specific errors**: Over-engineered for Silver tier

---

## Best Practices Established

### 1. Environment Configuration

- All configuration via environment variables
- Zod schema for environment validation at startup
- `.env.example` provided (no `.env` in version control)
- Runtime-only secrets (AI_API_KEY not stored)

### 2. Database Migrations

- All schema changes via Prisma migrations
- Migration files committed to version control
- Rollback strategy documented
- Seed data optional for development

### 3. API Design

- RESTful conventions (POST /tasks, GET /tasks/:id, etc.)
- Consistent response format
- Pagination for list endpoints (activity logs)
- Standard HTTP status codes (200, 201, 400, 404, 500)

### 4. Logging

- Structured logging (JSON format in production)
- Request/response logging middleware
- Activity logs separate from application logs
- Log levels: error, warn, info, debug

### 5. Security (Silver-tier appropriate)

- No secrets in source code
- CORS configurable via environment
- Input validation on all endpoints
- Error messages don't leak internals
- No authentication (per spec clarification)

---

## Integration Patterns

### 1. Task Status Transitions

**Pattern**: Service-layer validation with explicit state machine

```typescript
async updateTaskStatus(id: string, newStatus: TaskStatus): Promise<Task> {
  const task = await this.taskRepository.findById(id);
  
  // Enforce linear progression: Pending → In Progress → Done
  if (!this.isValidTransition(task.status, newStatus)) {
    throw new ValidationError('Invalid status transition');
  }
  
  return this.taskRepository.update(id, { status: newStatus });
}
```

**Valid transitions**:
- Pending → In Progress
- In Progress → Done
- (No backward transitions allowed)

---

### 2. Plan Generation Flow

**Pattern**: AI provider abstraction with fallback

```typescript
async generatePlanForTask(taskId: string): Promise<Plan> {
  const task = await this.taskService.getTask(taskId);
  
  try {
    const steps = await this.aiProvider.generatePlan(task);
    return this.planService.create({ taskId, steps });
  } catch (error) {
    // Log error, return 503 Service Unavailable
    throw new ServiceUnavailableError('AI service unavailable');
  }
}
```

---

### 3. System State Machine

**Pattern**: Explicit state transitions triggered by events

```typescript
enum SystemState {
  Idle = 'Idle',
  Thinking = 'Thinking',
  Planning = 'Planning'
}

async setState(newState: SystemState): Promise<void> {
  await this.stateRepository.update({
    state: newState,
    lastActivity: new Date()
  });
}

// State transitions triggered by service events
// Task received → Idle → Thinking
// Analysis complete → Thinking → Planning
// Plan delivered → Planning → Idle
```

---

### 4. Activity Logging

**Pattern**: Service-layer logging with structured data

```typescript
async logActivity(type: string, description: string, metadata?: object): Promise<void> {
  await this.activityLogRepository.create({
    type,
    description,
    timestamp: new Date(),
    metadata
  });
}

// Logged events:
// - User actions: task.created, task.updated, plan.generated, etc.
// - System events: ai.invoked, state.changed, error.occurred
```

---

## Unresolved Questions

None. All technology decisions resolved for Silver-tier scope.

---

## References

- Express.js: https://expressjs.com/
- Prisma ORM: https://www.prisma.io/
- Zod: https://zod.dev/
- Jest: https://jestjs.io/
- Supertest: https://www.npmjs.com/package/supertest
