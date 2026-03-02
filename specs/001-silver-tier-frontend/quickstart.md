# Quickstart: Silver Tier Frontend

**Feature**: 001-silver-tier-frontend  
**Last Updated**: 2026-02-22

---

## Prerequisites

Before starting, ensure you have:

- ✅ Node.js 18+ installed
- ✅ Backend server running at an accessible URL
- ✅ Git branch `001-silver-tier-frontend` checked out

---

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Install TanStack Query

```bash
npm install @tanstack/react-query@^5
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env.local

# Edit .env.local and set your backend URL
# For local development:
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# For production:
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

### 4. Verify Backend Connection

Before starting the frontend, ensure the backend is running:

```bash
# Test the API endpoint
curl http://localhost:8000/api/v1/system/state
```

Expected response:
```json
{
  "status": "idle",
  "lastActivityAt": "2026-02-22T00:00:00Z",
  "currentTaskId": null
}
```

### 5. Start Development Server

```bash
npm run dev
```

The application will start at `http://localhost:3000`

---

## Verify Connection

Once the application loads, verify the following:

| Check | Expected Result |
|-------|-----------------|
| Dashboard loads | Tasks display from backend (not mock data) |
| Agent status | Shows current state (idle/processing/working) |
| Activity feed | Displays recent activity logs |
| Create task | New task persists to backend |
| Update status | Status change reflects immediately |

### Browser DevTools Check

Open browser DevTools → Network tab:

1. Filter by `tasks`, `system/state`, `activity`
2. All requests should show status `200`
3. Response data should match OpenAPI contracts

---

## Development Workflow

### Running Tests

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Test with coverage
npm test -- --coverage
```

### Code Quality

```bash
# Type checking
npx tsc --noEmit

# Linting
npm run lint

# Format
npx prettier --write "src/**/*.{ts,tsx}"
```

### Building for Production

```bash
npm run build
npm run start
```

---

## Troubleshooting

### API Errors (Connection Refused)

**Problem**: Network requests fail with `ERR_CONNECTION_REFUSED`

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/api/v1/system/state`
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Restart dev server after env changes

---

### CORS Errors

**Problem**: Console shows CORS policy errors

**Solution**:
1. Ensure backend allows origin `http://localhost:3000`
2. Check backend CORS configuration:
   ```javascript
   // Backend CORS config
   app.use(cors({
     origin: ['http://localhost:3000', 'https://yourdomain.com']
   }));
   ```

---

### Empty Data on Dashboard

**Problem**: Dashboard loads but shows no tasks/activities

**Solution**:
1. Check backend has data in database
2. Verify API endpoints return data: `curl http://localhost:8000/api/v1/tasks`
3. Check browser console for JavaScript errors
4. Verify TanStack Query is properly configured in `layout.tsx`

---

### TypeScript Errors

**Problem**: `tsc` shows type errors

**Solution**:
1. Ensure all type definitions in `src/types/` match API responses
2. Run `npm install` to ensure all dependencies are installed
3. Check Zod schemas in `src/lib/validations.ts` match API contracts

---

### Dark Mode Issues

**Problem**: Dark mode doesn't toggle correctly

**Solution**:
1. Verify `next-themes` or similar is configured
2. Check all components use Tailwind `dark:` classes
3. Ensure no hardcoded colors in custom CSS

---

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # React components
│   │   ├── ui/          # shadcn/ui base components
│   │   ├── dashboard/   # Dashboard-specific components
│   │   └── shared/      # Reusable components
│   ├── hooks/           # TanStack Query hooks
│   ├── lib/             # Utilities and API client
│   ├── types/           # TypeScript type definitions
│   └── styles/          # Global styles
├── tests/
│   ├── unit/            # Jest unit tests
│   └── e2e/             # Playwright E2E tests
├── .env.local           # Local environment (gitignored)
├── .env.example         # Environment template
└── package.json
```

---

## Key Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm test` | Run Jest tests |
| `npm run test:e2e` | Run Playwright E2E tests |
| `npx tsc --noEmit` | Type check without emitting |

---

## Next Steps

After setup:

1. Review `specs/001-silver-tier-frontend/plan.md` for implementation phases
2. Follow Phase 2 tasks in order
3. Run tests after each phase
4. Update this quickstart if you add new setup steps

---

## Support

For issues or questions:

- Check `plan.md` for architecture details
- Review `data-model.md` for type definitions
- See `contracts/*.yaml` for API specifications
