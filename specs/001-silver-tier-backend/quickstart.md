# Quickstart Guide: Silver Tier Backend

**Date**: 2026-02-22
**Feature**: Silver Tier Backend
**Branch**: 001-silver-tier-backend

## Prerequisites

- Node.js 20.x (LTS)
- npm or yarn
- PostgreSQL 14+ (local or Docker)
- Docker (optional, for containerized deployment)

---

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
cd backend
npm install
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/ai_employee?schema=public"

# AI Provider
AI_PROVIDER="anthropic"
AI_API_KEY="your-api-key-here"

# Server
NODE_ENV="development"
PORT=3000
CORS_ORIGIN="*"
```

### 3. Start PostgreSQL (Docker option)

```bash
docker-compose up -d postgres
```

Or use your local PostgreSQL installation and create the database:

```bash
createdb ai_employee
```

### 4. Run Database Migrations

```bash
npx prisma migrate dev
```

### 5. Start the Server

```bash
npm run dev
```

Server will start on `http://localhost:3000`

---

## Verify Installation

### Health Check

```bash
curl http://localhost:3000/api/v1/system/health
```

Expected response:
```json
{
  "data": {
    "status": "healthy",
    "uptime": 10,
    "timestamp": "2026-02-22T00:00:00Z"
  }
}
```

### Check System State

```bash
curl http://localhost:3000/api/v1/system/state
```

Expected response:
```json
{
  "data": {
    "state": "Idle",
    "lastActivity": "2026-02-22T00:00:00Z"
  }
}
```

---

## First API Calls

### Create a Task

```bash
curl -X POST http://localhost:3000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn the API",
    "description": "Explore all endpoints and understand the system"
  }'
```

### List Tasks

```bash
curl http://localhost:3000/api/v1/tasks
```

### Update Task Status

```bash
curl -X PATCH http://localhost:3000/api/v1/tasks/{task-id}/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "In Progress"
  }'
```

### Generate a Plan

```bash
curl -X POST http://localhost:3000/api/v1/tasks/{task-id}/plans
```

### View Activity Log

```bash
curl http://localhost:3000/api/v1/activity-logs
```

---

## Development Commands

```bash
# Run development server with hot reload
npm run dev

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Build for production
npm run build

# Run production server
npm start

# Generate Prisma client
npm run prisma:generate

# Create new migration
npm run prisma:migrate

# Open Prisma Studio (database GUI)
npm run prisma:studio

# Lint code
npm run lint
```

---

## Docker Deployment

### Build Image

```bash
docker build -t ai-employee-backend:latest .
```

### Run Container

```bash
docker run -d \
  --name ai-employee-backend \
  -p 3000:3000 \
  --env-file .env \
  ai-employee-backend:latest
```

### Docker Compose (Full Stack)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## Troubleshooting

### Database Connection Fails

**Error**: `Can't reach database server at localhost:5432`

**Solutions**:
1. Ensure PostgreSQL is running: `pg_isready`
2. Check DATABASE_URL in `.env`
3. Verify database exists: `psql -l | grep ai_employee`

### Prisma Client Errors

**Error**: `Prisma Client could not find the query engine`

**Solution**:
```bash
npx prisma generate
```

### Port Already in Use

**Error**: `EADDRINUSE: address already in use :::3000`

**Solutions**:
1. Change PORT in `.env`
2. Find and kill process: `lsof -i :3000` then `kill -9 <PID>`

### AI Provider Errors

**Error**: `AI service is temporarily unavailable`

**Solutions**:
1. Verify AI_API_KEY is set correctly
2. Check AI provider status
3. Review logs for detailed error

---

## Project Structure

```
backend/
├── src/
│   ├── index.ts              # Entry point
│   ├── app.ts                # Express app
│   ├── config/               # Configuration
│   ├── services/             # Business logic
│   ├── controllers/          # HTTP handlers
│   ├── routes/               # API routes
│   ├── middleware/           # Express middleware
│   ├── models/               # Type definitions
│   └── ai/                   # AI provider abstraction
├── prisma/
│   ├── schema.prisma         # Database schema
│   └── migrations/           # Database migrations
├── tests/
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── .env.example              # Environment template
├── Dockerfile                # Docker config
└── package.json              # Dependencies
```

---

## API Documentation

Full API documentation available at:
- OpenAPI/Swagger: `http://localhost:3000/api-docs` (if enabled)
- Contract documentation: `./contracts/api-contract.md`

---

## Next Steps

1. **Explore the API**: Try all endpoints using curl or Postman
2. **Run Tests**: `npm test` to verify everything works
3. **Read the Docs**: Review `data-model.md` and `api-contract.md`
4. **Start Developing**: Begin implementing new features

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs: `docker-compose logs` or check `logs/` directory
3. Consult the specification: `spec.md`
4. Review the implementation plan: `plan.md`
