# Ralph Wiggum Autonomous Loop (Gold Tier)

This module provides the autonomous reasoning loop for the AI Employee.

## Components

### 1. `ralph_loop.py` (Active Orchestrator)
The primary execution engine that runs the AI Agent CLI (Claude/Gemini) in a loop until tasks in `AI-Employee-Vault/Needs_Action/` are completed.

**Features:**
- **Stop Hook:** Ensures the agent continues until task completion.
- **State Reinjection:** Pass context between iterations if the agent exits.
- **Completion Detection:** Detects `<promise>TASK_COMPLETE</promise>` or file movement.
- **Max Iterations:** Safety limit to prevent infinite loops.

**Usage:**
```bash
# Run with Claude (default)
python ralph_loop.py

# Run with Gemini
python ralph_loop.py --agent gemini

# Set max iterations
python ralph_loop.py --max-iters 20
```

### 2. `ralph_wiggum_loop.py` (Perception Engine)
A daemon-style loop that implements the PERCEIVE → REASON → DECIDE → ACT → LEARN cycle. It scans various sources (Gmail, WhatsApp, Odoo) and populates the Vault with tasks.

## Completion Strategies

- **Strategy 1:** Agent outputs `<promise>TASK_COMPLETE</promise>` in the final response.
- **Strategy 2:** Agent moves the task file from `/Needs_Action` to `/Done` using filesystem tools.

## Folder Structure

- `AI-Employee-Vault/Needs_Action/`: Pending tasks.
- `AI-Employee-Vault/Done/`: Completed tasks.
- `AI-Employee-Vault/Logs/`: Loop execution logs.
- `AI-Employee-Vault/.ralph_loop_state.json`: Current loop state for recovery.
