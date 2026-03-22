# Data Model: Platinum Tier Backend

**Feature**: Platinum Tier Backend Upgrade
**Date**: 2026-03-08

## Entities

### Goal
- **id**: UUID (Primary Key)
- **title**: String
- **description**: Text
- **state**: Enum (PENDING_PLAN, PENDING_APPROVAL, ACTIVE, COMPLETED, FAILED, PAUSED)
- **priority**: Integer (1-10)
- **user_id**: UUID (Foreign Key to User)
- **created_at**: DateTime
- **updated_at**: DateTime
- **metadata**: JSONB (e.g., target deadline, constraints)

### Task
- **id**: UUID (Primary Key)
- **goal_id**: UUID (Foreign Key to Goal)
- **title**: String
- **description**: Text
- **status**: Enum (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED)
- **order**: Integer (Decomposition sequence)
- **assigned_agent**: String (TaskAnalyzer, Planner, etc.)
- **depends_on**: UUID[] (List of task IDs this task depends on)
- **created_at**: DateTime
- **updated_at**: DateTime

### AgentExecution
- **id**: UUID (Primary Key)
- **task_id**: UUID (Foreign Key to Task)
- **agent_name**: String
- **reasoning**: Text (Thought process before action)
- **tool_calls**: JSONB (List of tool invocations)
- **output**: Text (Final result or error message)
- **status**: Enum (SUCCESS, FAILURE)
- **created_at**: DateTime

### MemoryRecord
- **id**: UUID (Primary Key)
- **content**: Text
- **embedding**: Vector(1536) (pgvector for semantic search)
- **goal_id**: UUID (Optional - context source)
- **task_id**: UUID (Optional - context source)
- **user_id**: UUID (Foreign Key to User)
- **created_at**: DateTime

### CostLog
- **id**: UUID (Primary Key)
- **agent_execution_id**: UUID (Optional - context of cost)
- **model_name**: String (e.g., gpt-4, claude-3)
- **tokens_in**: Integer
- **tokens_out**: Integer
- **estimated_cost_usd**: Decimal(10, 6)
- **created_at**: DateTime

### ToolInvocation
- **id**: UUID (Primary Key)
- **agent_execution_id**: UUID (Foreign Key to AgentExecution)
- **tool_name**: String (MCP compatible)
- **arguments**: JSONB
- **result**: JSONB
- **risk_score**: Float (Calculated by RiskAssessmentAgent)
- **status**: Enum (PENDING_APPROVAL, EXECUTED, REJECTED, FAILED)
- **created_at**: DateTime

## Relationships
- **Goal** has many **Tasks**.
- **Task** has many **AgentExecutions**.
- **AgentExecution** has many **ToolInvocations**.
- **AgentExecution** has one **CostLog**.
- **MemoryRecord** belongs to a **User** (Global recall for that user).
