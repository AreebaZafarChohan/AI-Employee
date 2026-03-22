# Data Model: Platinum Tier Frontend

All types represent the frontend TypeScript interfaces consumed from backend API responses.

## Agent

```typescript
interface Agent {
  id: string;
  name: string;
  type: string;           // e.g., "planner", "memory", "risk"
  status: "running" | "stopped" | "error";
  errorMessage?: string;
  createdAt: string;      // ISO 8601
  updatedAt: string;
}

interface AgentLogEntry {
  id: string;
  agentId: string;
  level: "info" | "warn" | "error";
  message: string;
  timestamp: string;      // ISO 8601
  metadata?: Record<string, unknown>;
}
```

## Goal

```typescript
interface Goal {
  id: string;
  title: string;
  description: string;
  priority: "low" | "medium" | "high" | "critical";
  status: "draft" | "active" | "completed" | "cancelled";
  progress: number;       // 0-100
  tasks: Task[];
  createdAt: string;
  updatedAt: string;
}

// State transitions: draft → active → completed; cancel from draft|active
```

## Task

```typescript
interface Task {
  id: string;
  goalId: string;
  title: string;
  status: "pending" | "in-progress" | "completed" | "failed";
  assignedAgentId?: string;
  createdAt: string;
  updatedAt: string;
}
```

## Memory Entry

```typescript
interface MemoryEntry {
  id: string;
  content: string;
  source: string;
  agentId?: string;
  similarityScore?: number;  // 0.0-1.0, present in search results
  metadata: Record<string, unknown>;
  createdAt: string;
}
```

## Cost Record

```typescript
interface CostRecord {
  id: string;
  agentId: string;
  agentName: string;
  model: string;
  tokenCount: number;
  costAmount: number;      // USD
  timestamp: string;
}

interface CostSummary {
  totalCost: number;
  totalTokens: number;
  totalRequests: number;
  period: "day" | "week" | "month";
  breakdown: {
    byAgent: { agentId: string; agentName: string; cost: number; tokens: number }[];
    byModel: { model: string; cost: number; tokens: number }[];
  };
  timeSeries: { date: string; cost: number; tokens: number }[];
}
```

## Tool Invocation

```typescript
interface ToolInvocation {
  id: string;
  toolName: string;
  status: "pending" | "success" | "failure";
  inputParams: Record<string, unknown>;
  output?: unknown;
  errorDetails?: string;
  durationMs?: number;
  agentId?: string;
  timestamp: string;
}
```

## Queue

```typescript
interface QueueHealth {
  name: string;
  depth: number;
  processingRate: number;  // items per minute
  status: "healthy" | "warning" | "critical";
}
```

## System Intelligence

```typescript
interface ActivityHeatmapData {
  agentId: string;
  agentName: string;
  buckets: { timeBucket: string; intensity: number }[];  // intensity 0.0-1.0
}

interface ExecutionTimelineEvent {
  id: string;
  agentId: string;
  agentName: string;
  taskTitle: string;
  startTime: string;
  endTime?: string;
  status: "running" | "completed" | "failed";
}
```

## Relationships

- Goal 1→N Task
- Agent 1→N AgentLogEntry
- Agent 1→N CostRecord
- Agent 0→N ToolInvocation
- Agent 0→N MemoryEntry
