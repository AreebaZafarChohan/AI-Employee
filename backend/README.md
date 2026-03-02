# AI Employee Backend API

Silver Tier Backend - Production-grade Node.js/TypeScript REST API for task management, plan generation, and system monitoring.

## Quick Start

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start PostgreSQL (Docker)
docker-compose up -d postgres

# Run migrations
npx prisma migrate dev

# Start development server
npm run dev
```

Server runs on `http://localhost:3000`

## API Endpoints

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tasks` | Create a new task |
| GET | `/api/v1/tasks` | List all tasks |
| GET | `/api/v1/tasks/:id` | Get task by ID |
| PATCH | `/api/v1/tasks/:id` | Update task |
| PATCH | `/api/v1/tasks/:id/status` | Update task status |
| DELETE | `/api/v1/tasks/:id` | Delete task |

### Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tasks/:taskId/plans` | Generate plan for task |
| GET | `/api/v1/plans` | List all plans |
| GET | `/api/v1/plans/:id` | Get plan by ID |
| PATCH | `/api/v1/plans/:id/status` | Update plan status |
| DELETE | `/api/v1/plans/:id` | Delete plan |

### Activity Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/activity-logs` | List activity logs |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/system/state` | Get system state |
| GET | `/api/v1/system/health` | Health check |

## Example Usage

### Create a Task

```bash
curl -X POST http://localhost:3000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn the API",
    "description": "Explore all endpoints"
  }'
```

### Generate a Plan

```bash
curl -X POST http://localhost:3000/api/v1/tasks/{task-id}/plans
```

### Update Task Status

```bash
curl -X PATCH http://localhost:3000/api/v1/tasks/{task-id}/status \
  -H "Content-Type: application/json" \
  -d '{"status": "In Progress"}'
```

## Development Commands

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Build for production
npm run build

# Run production server
npm start

# Lint code
npm run lint

# Database commands
npm run prisma:generate   # Generate Prisma client
npm run prisma:migrate    # Run migrations
npm run prisma:studio     # Open Prisma Studio
npm run prisma:seed       # Seed database
```

## Project Structure

```
backend/
├── src/
│   ├── config/          # Configuration loaders
│   ├── controllers/     # HTTP request handlers
│   ├── middleware/      # Express middleware
│   ├── models/          # Type definitions
│   ├── routes/          # API routes
│   ├── services/        # Business logic
│   ├── ai/              # AI provider abstraction
│   ├── utils/           # Utilities (logger, errors)
│   ├── app.ts           # Express app setup
│   └── index.ts         # Entry point
├── prisma/
│   ├── schema.prisma    # Database schema
│   ├── migrations/      # Database migrations
│   └── seed.ts          # Seed data
├── tests/
│   ├── integration/     # API tests
│   └── unit/            # Unit tests
└── Dockerfile           # Docker config
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `AI_PROVIDER` | AI provider (anthropic, mock) | `mock` |
| `AI_API_KEY` | AI API key | - |
| `NODE_ENV` | Environment | `development` |
| `PORT` | Server port | `3000` |
| `CORS_ORIGIN` | Allowed origins | `*` |

## Testing

```bash
# Run all tests
npm test

# Run specific test file
npm test -- tasks.test.ts

# Run tests in watch mode
npm run test:watch
```

## Docker

```bash
# Build image
docker build -t ai-employee-backend .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

## License

MIT
