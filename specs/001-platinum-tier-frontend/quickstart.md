# Quickstart: Platinum Tier Frontend

## Prerequisites

- Node.js 18+
- Backend running at `http://localhost:3001` (or configured via env)

## Setup

```bash
cd frontend
npm install
```

## Environment

Create/update `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:3001
```

## Run

```bash
npm run dev
```

Open `http://localhost:3000`.

## New Pages

| Route | Feature |
| ----- | ------- |
| /agents | Agent Control Panel |
| /goals | Goal Management |
| /memory | Memory Explorer |
| /costs | Cost Dashboard |
| /tools | Tool Execution Monitor |
| /intelligence | System Intelligence Dashboard |

## Test

```bash
npm test                 # Unit tests
npm run test:e2e         # E2E tests
```

## Verify

1. Navigate to /agents — see agent list with status badges
2. Navigate to /goals — create a goal, see it listed
3. Navigate to /memory — search, see results with scores
4. Navigate to /costs — see summary cards and charts
5. Navigate to /tools — see invocation list with real-time updates
6. Navigate to /intelligence — see heatmap, timeline, queue health
7. Disconnect backend — see connection lost banner, auto-reconnect
