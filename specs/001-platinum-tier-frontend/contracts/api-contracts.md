# API Contracts: Platinum Tier Frontend

Base URL: `${NEXT_PUBLIC_API_URL}` (environment variable)

## Agents

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /api/agents | List all agents |
| POST | /api/agents/:id/start | Start an agent |
| POST | /api/agents/:id/stop | Stop an agent |
| GET | /api/agents/:id/logs?level=&limit=&offset= | Get agent logs (paginated) |

**WebSocket**: `ws://.../ws/agents` — pushes `agent:status` and `agent:log` events.

## Goals

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /api/goals | List all goals |
| POST | /api/goals | Create a goal |
| GET | /api/goals/:id | Get goal with tasks |
| PATCH | /api/goals/:id | Update goal (status transitions) |
| DELETE | /api/goals/:id | Cancel a goal |

## Memory

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /api/memory/search?q=&limit=&offset= | Search memory entries |
| GET | /api/memory/:id | Get memory entry detail |

## Costs

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /api/costs/summary?period=day\|week\|month | Get cost summary with breakdowns |
| GET | /api/costs/timeseries?period=&from=&to= | Get cost time series |

## Tools

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /api/tools/invocations?limit=&offset= | List tool invocations (paginated) |
| GET | /api/tools/invocations/:id | Get invocation detail |

**WebSocket**: `ws://.../ws/tools` — pushes `tool:invocation` events.

## System Intelligence

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /api/intelligence/heatmap?period= | Agent activity heatmap data |
| GET | /api/intelligence/timeline?from=&to= | Execution timeline events |
| GET | /api/intelligence/queues | Queue health status |

## Error Response Format

```json
{
  "error_code": "string",
  "message": "string",
  "details": {}
}
```
