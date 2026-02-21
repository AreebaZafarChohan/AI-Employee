# CLI Interface Contract: Personal AI Employee – Bronze Tier

## Overview
This document defines the command-line interface contract for the Personal AI Employee Bronze Tier implementation. The CLI serves as the primary interface for manual execution as specified in the requirements.

## Commands

### 1. Initialize Vault
```
python -m src.cli.main init --vault-path <path>
```

#### Purpose
Creates the initial Obsidian vault structure with required files and folders.

#### Parameters
- `--vault-path` (required): Path to the directory where the vault should be created

#### Expected Behavior
- Creates the vault directory if it doesn't exist
- Creates Dashboard.md and Company_Handbook.md files
- Creates /Needs_Action, /Plans, and /Done folders (FR-002)
- Returns success/error status

#### Success Response
```
Vault initialized successfully at: <path>
- Created Dashboard.md
- Created Company_Handbook.md
- Created folder structure: Needs_Action, Plans, Done
```

#### Error Response
```
Error: Could not initialize vault at <path>
Reason: <specific reason>
```

### 2. Configure System
```
python -m src.cli.main configure --watch-path <path> --vault-path <path>
```

#### Purpose
Configures the file system watcher and vault paths.

#### Parameters
- `--watch-path` (required): Directory to monitor for new input files
- `--vault-path` (required): Path to the Obsidian vault

#### Expected Behavior
- Validates that both paths exist and are accessible
- Creates or updates configuration file
- Verifies file system watcher can access the watch directory

#### Success Response
```
Configuration saved successfully
- Watching: <watch-path>
- Vault: <vault-path>
```

#### Error Response
```
Error: Could not save configuration
Reason: <specific reason>
```

### 3. Process Tasks
```
python -m src.cli.main process
```

#### Purpose
Manually executes the processing workflow: checks for new inputs, processes them with Claude, and manages the vault workflow.

#### Parameters
- None required

#### Expected Behavior
- Checks watched directory for new files
- Moves new files to /Needs_Action folder in vault
- Processes files in /Needs_Action with Claude to create plans in /Plans
- Implements error handling with retries (FR-016)
- Processes each task within 30 seconds (FR-014)
- Logs all operations

#### Success Response
```
Processing completed
- Found <n> new tasks
- Processed <n> tasks with Claude
- Created <n> plans in /Plans folder
- Duration: <time> seconds
```

#### Error Response
```
Error during processing:
- Failed to process <n> tasks
- Error details: <specific errors>
- Retry attempts: <number>
```

### 4. Complete Task
```
python -m src.cli.main complete --plan-id <id>
```

#### Purpose
Moves a completed plan from /Plans to /Done folder.

#### Parameters
- `--plan-id` (required): ID of the plan to mark as complete

#### Expected Behavior
- Finds the plan with the specified ID in /Plans folder
- Moves it to /Done folder
- Updates the plan's status to completed
- Applies data retention policy (FR-015)

#### Success Response
```
Task completed successfully
- Plan <id> moved to /Done folder
- Status updated to completed
```

#### Error Response
```
Error: Could not complete task
Reason: Plan with ID <id> not found in /Plans
```

### 5. Test/Smoke Test
```
python -m src.cli.main test
```

#### Purpose
Runs a series of verification checks to ensure the system is functioning correctly.

#### Parameters
- None required

#### Expected Behavior
- Verifies vault structure exists correctly
- Tests file watcher functionality with a sample file
- Verifies Claude processing works with a simple task
- Checks that all folder transitions work properly
- Validates security measures like input sanitization (FR-013)

#### Success Response
```
All tests passed successfully
- Vault structure: OK
- File watcher: OK
- Claude processing: OK
- Folder transitions: OK
- Security measures: OK
```

#### Error Response
```
Test failures detected:
- <specific component>: FAIL - <reason>
- <another component>: FAIL - <reason>
```

## Error Handling Contract

### Standard Error Format
All errors follow this format:
```
Error: <brief description>
Code: <error code>
Details: <detailed information>
Timestamp: <ISO 8601 timestamp>
```

### Retry Mechanism
- Transient failures are automatically retried up to 3 times (FR-016)
- Exponential backoff is used between retries
- Final error is reported after all retries are exhausted

### Logging Contract
- All operations are logged to application logs
- Processing times are recorded for performance monitoring (FR-014)
- Security-related events are logged separately
- Log rotation is implemented to prevent excessive storage usage

## Performance Contract

### Processing Time Limits
- Individual tasks: Maximum 30 seconds (FR-014)
- Batch processing: Scales linearly with number of tasks
- Error handling: Additional time allowed for retry mechanisms

### Resource Usage
- Memory usage: Less than 100MB during normal operation
- File system: Atomic operations to prevent corruption
- API calls: Respectful of Claude API rate limits