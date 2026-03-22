# Multi-Agent Coordination System

This document outlines the collaboration protocol for the "AI Employee" system, enabling coordination between **Cloud Agent** and **Local Agent** via a synchronized Obsidian vault.

## 1. Core Concept

The system uses a **filesystem-based coordination** model. The shared Obsidian vault acts as the "database" and state of truth.
- **Synchronization**: The vault is synced (e.g., via Syncthing, Dropbox, or Git) between the Local and Cloud environments.
- **Atomicity**: Task ownership is determined by atomic file moves (the "Claim-by-Move" pattern).

## 2. Directory Structure

The coordination relies on a strict folder hierarchy within `AI-Employee-Vault`:

```
AI-Employee-Vault/
├── Needs_Action/           # Inbox for new tasks
│   ├── email/
│   ├── social/
│   ├── accounting/
│   ├── marketing/
│   └── tasks/
├── In_Progress/            # Active workspace
│   ├── Local_Agent/        # Tasks claimed by Local Agent
│   └── Cloud_Agent/        # Tasks claimed by Cloud Agent
├── Pending_Approval/       # Tasks waiting for human/supervisor review
│   └── ... (by domain)
├── Done/                   # Completed tasks archive
├── Errors/                 # Failed tasks
└── Logs/                   # System logs
```

## 3. Coordination Algorithm

### 3.1. Heartbeat
Each agent writes to a heartbeat file every 30-60 seconds to signal it is online.
- Path: `In_Progress/<Agent_ID>/heartbeat.json`
- Content: `{"agent_id": "...", "timestamp": 1234567890, "status": "active"}`

### 3.2. Task Claiming (The "Claim-by-Move" Pattern)
To prevent duplicate work, agents follow this strict protocol:

1.  **Scan**: Agent looks for files in `Needs_Action/<domain>`.
2.  **Select**: Agent picks a file (e.g., `invoice_123.md`).
3.  **Attempt Claim**: Agent attempts to **move** the file to `In_Progress/<Agent_ID>/invoice_123.md`.
    -   *Success*: The move operation completed without error. The agent **owns** the task.
    -   *Failure (File Not Found)*: Another agent beat you to it. Abort and pick another task.
4.  **Execute**: Agent processes the file in its private `In_Progress` folder.

### 3.3. Conflict Prevention
- **Atomic Moves**: Operating systems guarantee that a file cannot be moved to two places simultaneously. If two agents try to move the same file at the exact same moment, one will succeed, and the other will get a `FileNotFoundError` (or similar).
- **Isolation**: Once in `In_Progress/<Agent_ID>/`, no other agent touches the file.

## 4. Python Implementation

The logic is encapsulated in `src/agent_coordinator.py`.

### Key Methods
- `claim_task(task_file)`: Handles the atomic move and error catching.
- `heartbeat()`: Updates presence.
- `complete_task(task_file)`: Moves finished work to `Done` or `Pending_Approval`.

## 5. Example Workflows

### Scenario A: Processing an Invoice (Cloud Agent)
1.  **Trigger**: New email arrives. `gmail_watcher` saves `invoice_dec.md` to `Needs_Action/accounting/`.
2.  **Claim**: Cloud Agent scans `Needs_Action/accounting/`, finds `invoice_dec.md`.
3.  **Move**: Cloud Agent moves it to `In_Progress/Cloud_Agent/invoice_dec.md`.
4.  **Work**: Agent extracts data, updates Quickbooks.
5.  **Finish**: Agent moves file to `Done/invoice_dec.md` and appends a "Completion Report" section to the markdown.

### Scenario B: Social Media Post (Local Agent)
1.  **Trigger**: User drops a raw idea `viral_tweet.md` into `Needs_Action/social/`.
2.  **Claim**: Local Agent claims it to `In_Progress/Local_Agent/viral_tweet.md`.
3.  **Work**: Agent generates image and copy.
4.  **Review**: Agent moves file to `Pending_Approval/social/viral_tweet.md`.
5.  **Approval**: User reviews in Obsidian, moves file back to `Needs_Action/social/` (or a specific `Approved` folder) for final posting.

## 6. Logging
All state changes are appended to `Logs/coordination_log.md` for debugging and audit trails.
Format: `| Timestamp | Agent | Action | File |`
