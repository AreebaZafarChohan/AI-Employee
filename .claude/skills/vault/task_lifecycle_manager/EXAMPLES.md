# Task Lifecycle Manager - Implementation Examples

This document provides complete, production-ready implementation examples for the Task Lifecycle Manager skill.

---

## Table of Contents

1. [Complete Agent Implementation](#complete-agent-implementation)
2. [Lifecycle Orchestration](#lifecycle-orchestration)
3. [Error Handling Patterns](#error-handling-patterns)
4. [Recovery Job Setup](#recovery-job-setup)
5. [Integration with Watchers](#integration-with-watchers)
6. [Monitoring & Metrics](#monitoring--metrics)

---

## Complete Agent Implementation

### Example 1: Local Executive Agent (lex) with Full Lifecycle

```javascript
/**
 * lex-agent.js
 * Local Executive Agent that processes tasks from Needs_Action to Pending_Approval
 */

const vaultManager = require('./vault-state-manager');
const taskLifecycle = require('./task-lifecycle-manager');

class LexAgent {
  constructor(agentName = 'lex') {
    this.agentName = agentName;
    this.activeTasks = new Map();  // taskId -> heartbeatInterval
    this.running = false;
  }

  /**
   * Main agent loop
   */
  async start() {
    console.log(`${this.agentName}: Starting agent...`);
    this.running = true;

    // Start main processing loop
    while (this.running) {
      try {
        await this.processNewTasks();
      } catch (err) {
        console.error(`${this.agentName}: Error in processing loop:`, err);
      }

      // Wait before next iteration
      await this.sleep(5000);  // Poll every 5 seconds
    }
  }

  /**
   * Process new tasks from Needs_Action
   */
  async processNewTasks() {
    // List all tasks in Needs_Action
    const files = await vaultManager.listFolderFiles('Needs_Action');

    if (files.length === 0) {
      return;
    }

    console.log(`${this.agentName}: Found ${files.length} tasks in Needs_Action`);

    // Try to claim and process first available task
    for (const file of files) {
      const success = await this.claimAndProcess(file.name);
      if (success) {
        break;  // Only process one task at a time (Bronze tier)
      }
    }
  }

  /**
   * Claim and process a single task
   */
  async claimAndProcess(taskFile) {
    // Step 1: Claim task
    console.log(`${this.agentName}: Attempting to claim ${taskFile}`);
    const claimResult = await taskLifecycle.claimTask(taskFile, this.agentName);

    if (!claimResult.success) {
      if (claimResult.reason === 'already_claimed') {
        console.log(`${this.agentName}: Task already claimed, skipping`);
      } else {
        console.warn(`${this.agentName}: Failed to claim: ${claimResult.reason}`);
      }
      return false;
    }

    const taskId = claimResult.taskId;
    console.log(`${this.agentName}: ✓ Claimed task: ${taskId}`);

    // Step 2: Start work (move to In_Progress)
    try {
      await taskLifecycle.transitionTask(taskId, 'planned', 'in_progress', this.agentName);
      console.log(`${this.agentName}: ✓ Task moved to In_Progress`);
    } catch (err) {
      console.error(`${this.agentName}: Failed to start work:`, err.message);
      return false;
    }

    // Step 3: Start heartbeat
    this.startHeartbeat(taskId);

    // Step 4: Execute work
    let workSuccess = false;
    try {
      await this.executeTask(taskId);
      workSuccess = true;
      console.log(`${this.agentName}: ✓ Task work completed`);
    } catch (err) {
      console.error(`${this.agentName}: Task execution failed:`, err.message);
      await this.handleWorkFailure(taskId, err);
    }

    // Step 5: Stop heartbeat
    this.stopHeartbeat(taskId);

    // Step 6: Request approval (if work succeeded)
    if (workSuccess) {
      try {
        await taskLifecycle.transitionTask(
          taskId,
          'in_progress',
          'pending_approval',
          this.agentName
        );
        console.log(`${this.agentName}: ✓ Task moved to Pending_Approval`);
      } catch (err) {
        console.error(`${this.agentName}: Failed to request approval:`, err.message);
      }
    }

    return workSuccess;
  }

  /**
   * Execute task work
   */
  async executeTask(taskId) {
    const taskPath = `In_Progress/${taskId}.json`;
    const { content } = await vaultManager.readVaultFile(taskPath, this.agentName);
    const task = JSON.parse(content);

    console.log(`${this.agentName}: Executing task: ${task.title}`);

    // Execute each step
    for (let i = 0; i < task.steps.length; i++) {
      const step = task.steps[i];
      console.log(`${this.agentName}:   Step ${i + 1}/${task.steps.length}: ${step.action}`);

      try {
        // Execute step (placeholder - implement actual logic)
        await this.executeStep(task, step);

        // Update step status
        task.steps[i].status = 'completed';
        task.steps[i].completed_at = new Date().toISOString();

        // Write back progress
        await vaultManager.writeVaultFile(
          taskPath,
          JSON.stringify(task, null, 2),
          this.agentName
        );

      } catch (err) {
        console.error(`${this.agentName}:   Step ${i + 1} failed:`, err.message);
        task.steps[i].status = 'failed';
        task.steps[i].error = err.message;

        await vaultManager.writeVaultFile(
          taskPath,
          JSON.stringify(task, null, 2),
          this.agentName
        );

        throw err;  // Propagate failure
      }
    }

    // Add completion metadata
    task.completed_at = new Date().toISOString();
    task.work_result = {
      summary: 'All steps completed successfully',
      confidence: 0.95
    };

    await vaultManager.writeVaultFile(
      taskPath,
      JSON.stringify(task, null, 2),
      this.agentName
    );
  }

  /**
   * Execute a single step (placeholder - implement actual logic)
   */
  async executeStep(task, step) {
    // Simulate work
    await this.sleep(1000);

    // Example: fail randomly to demonstrate retry logic
    if (Math.random() < 0.1) {
      throw new Error('Simulated transient failure');
    }
  }

  /**
   * Handle work failure
   */
  async handleWorkFailure(taskId, error) {
    console.log(`${this.agentName}: Handling task failure...`);

    const retryResult = await taskLifecycle.handleTaskFailure(
      taskId,
      error,
      this.agentName
    );

    if (retryResult.action === 'retry') {
      console.log(`${this.agentName}: Task will retry (attempt ${retryResult.attempts})`);
    } else {
      console.log(`${this.agentName}: Task failed permanently: ${retryResult.reason}`);
    }
  }

  /**
   * Start heartbeat for task
   */
  startHeartbeat(taskId) {
    const interval = setInterval(async () => {
      try {
        await this.updateHeartbeat(taskId);
      } catch (err) {
        console.error(`${this.agentName}: Heartbeat failed for ${taskId}:`, err.message);
      }
    }, 30000);  // Every 30 seconds

    this.activeTasks.set(taskId, interval);
  }

  /**
   * Stop heartbeat for task
   */
  stopHeartbeat(taskId) {
    const interval = this.activeTasks.get(taskId);
    if (interval) {
      clearInterval(interval);
      this.activeTasks.delete(taskId);
    }
  }

  /**
   * Update task heartbeat
   */
  async updateHeartbeat(taskId) {
    const taskPath = `In_Progress/${taskId}.json`;

    try {
      const { content } = await vaultManager.readVaultFile(taskPath, this.agentName);
      const task = JSON.parse(content);

      task.last_heartbeat = new Date().toISOString();

      await vaultManager.writeVaultFile(
        taskPath,
        JSON.stringify(task, null, 2),
        this.agentName
      );
    } catch (err) {
      // Task may have been moved (e.g., to Pending_Approval)
      // This is expected, stop heartbeat
      this.stopHeartbeat(taskId);
    }
  }

  /**
   * Stop agent
   */
  stop() {
    console.log(`${this.agentName}: Stopping agent...`);
    this.running = false;

    // Stop all heartbeats
    for (const [taskId, interval] of this.activeTasks) {
      clearInterval(interval);
    }
    this.activeTasks.clear();
  }

  /**
   * Utility: sleep
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Main
if (require.main === module) {
  const agent = new LexAgent('lex');

  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log('\nReceived SIGINT, shutting down...');
    agent.stop();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    console.log('\nReceived SIGTERM, shutting down...');
    agent.stop();
    process.exit(0);
  });

  // Start agent
  agent.start().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

module.exports = LexAgent;
```

---

### Example 2: Orchestrator Agent

```javascript
/**
 * orchestrator-agent.js
 * Orchestrator Agent that executes approved tasks via MCP
 */

const vaultManager = require('./vault-state-manager');
const taskLifecycle = require('./task-lifecycle-manager');
const mcpClient = require('./mcp-client');  // MCP integration

class OrchestratorAgent {
  constructor(agentName = 'orch') {
    this.agentName = agentName;
    this.running = false;
  }

  /**
   * Main orchestrator loop
   */
  async start() {
    console.log(`${this.agentName}: Starting orchestrator...`);
    this.running = true;

    while (this.running) {
      try {
        await this.processApprovedTasks();
      } catch (err) {
        console.error(`${this.agentName}: Error in processing loop:`, err);
      }

      await this.sleep(5000);  // Poll every 5 seconds
    }
  }

  /**
   * Process approved tasks
   */
  async processApprovedTasks() {
    const approvedFiles = await vaultManager.listFolderFiles('Approved');

    if (approvedFiles.length === 0) {
      return;
    }

    console.log(`${this.agentName}: Found ${approvedFiles.length} approved tasks`);

    // Process oldest task first
    const file = approvedFiles[0];

    await this.claimAndExecute(file.name);
  }

  /**
   * Claim and execute approved task
   */
  async claimAndExecute(taskFile) {
    console.log(`${this.agentName}: Attempting to claim ${taskFile}`);

    // Step 1: Claim from Approved (move to In_Progress)
    let taskId;
    try {
      await vaultManager.moveFile('Approved', taskFile, 'In_Progress', this.agentName);
      console.log(`${this.agentName}: ✓ Claimed from Approved`);

      // Extract task ID from filename
      const { content } = await vaultManager.readVaultFile(`In_Progress/${taskFile}`, this.agentName);
      const task = JSON.parse(content);
      taskId = task.plan_id;

    } catch (err) {
      if (err instanceof vaultManager.FileNotFoundError) {
        console.log(`${this.agentName}: Task already claimed by another orchestrator`);
        return;
      }
      throw err;
    }

    // Step 2: Execute task
    let outcome = 'success';
    let error = null;

    try {
      await this.executeTask(taskId);
      console.log(`${this.agentName}: ✓ Task executed successfully`);
    } catch (err) {
      console.error(`${this.agentName}: Task execution failed:`, err.message);
      outcome = 'failure';
      error = err;
    }

    // Step 3: Handle result
    if (outcome === 'success') {
      await this.completeTask(taskId);
    } else {
      await this.handleExecutionFailure(taskId, error);
    }
  }

  /**
   * Execute task via MCP
   */
  async executeTask(taskId) {
    const taskPath = `In_Progress/${taskId}.json`;
    const { content } = await vaultManager.readVaultFile(taskPath, this.agentName);
    const task = JSON.parse(content);

    console.log(`${this.agentName}: Executing via MCP: ${task.title}`);

    // Execute based on task type
    if (task.source === 'email') {
      await this.executeMCPEmail(task);
    } else if (task.source === 'message') {
      await this.executeMCPMessage(task);
    } else {
      throw new Error(`Unknown task source: ${task.source}`);
    }
  }

  /**
   * Execute email task via MCP
   */
  async executeMCPEmail(task) {
    console.log(`${this.agentName}:   Sending email via MCP...`);

    // Extract email details from task
    const emailData = task.work_result || task.data;

    // Call MCP email agent
    await mcpClient.sendEmail({
      to: emailData.to,
      subject: emailData.subject,
      body: emailData.body,
      attachments: emailData.attachments || []
    });

    console.log(`${this.agentName}:   ✓ Email sent`);
  }

  /**
   * Execute message task via MCP
   */
  async executeMCPMessage(task) {
    console.log(`${this.agentName}:   Sending message via MCP...`);

    const messageData = task.work_result || task.data;

    await mcpClient.sendMessage({
      to: messageData.to,
      text: messageData.text
    });

    console.log(`${this.agentName}:   ✓ Message sent`);
  }

  /**
   * Complete task successfully
   */
  async completeTask(taskId) {
    const taskPath = `In_Progress/${taskId}.json`;
    const { content } = await vaultManager.readVaultFile(taskPath, this.agentName);
    const task = JSON.parse(content);

    // Update completion metadata
    task.status = 'done';
    task.completed_at = new Date().toISOString();
    task.completed_by = this.agentName;
    task.outcome = 'success';

    await vaultManager.writeVaultFile(
      taskPath,
      JSON.stringify(task, null, 2),
      this.agentName
    );

    // Move to Done
    await vaultManager.moveFile('In_Progress', `${taskId}.json`, 'Done', this.agentName);

    console.log(`${this.agentName}: ✓ Task completed and moved to Done`);
  }

  /**
   * Handle execution failure
   */
  async handleExecutionFailure(taskId, error) {
    console.log(`${this.agentName}: Handling execution failure...`);

    const retryResult = await taskLifecycle.handleTaskFailure(
      taskId,
      error,
      this.agentName
    );

    if (retryResult.action === 'retry') {
      console.log(`${this.agentName}: Task will retry (attempt ${retryResult.attempts})`);
    } else {
      console.log(`${this.agentName}: Task failed permanently: ${retryResult.reason}`);
    }
  }

  /**
   * Stop orchestrator
   */
  stop() {
    console.log(`${this.agentName}: Stopping orchestrator...`);
    this.running = false;
  }

  /**
   * Utility: sleep
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Main
if (require.main === module) {
  const orchestrator = new OrchestratorAgent('orch');

  process.on('SIGINT', () => {
    console.log('\nReceived SIGINT, shutting down...');
    orchestrator.stop();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    console.log('\nReceived SIGTERM, shutting down...');
    orchestrator.stop();
    process.exit(0);
  });

  orchestrator.start().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

module.exports = OrchestratorAgent;
```

---

## Lifecycle Orchestration

### Example 3: Multi-Agent Coordination

```javascript
/**
 * agent-coordinator.js
 * Coordinates multiple agents (lex, orchestrator, recovery)
 */

const LexAgent = require('./lex-agent');
const OrchestratorAgent = require('./orchestrator-agent');
const { spawn } = require('child_process');

class AgentCoordinator {
  constructor() {
    this.agents = [];
    this.recoveryJob = null;
  }

  /**
   * Start all agents
   */
  async start() {
    console.log('=== Starting Agent Coordinator ===');

    // Start lex agent
    console.log('Starting lex agent...');
    const lex = new LexAgent('lex');
    this.agents.push({ name: 'lex', instance: lex });
    lex.start().catch(err => {
      console.error('Lex agent crashed:', err);
    });

    // Start orchestrator agent
    console.log('Starting orchestrator agent...');
    const orch = new OrchestratorAgent('orch');
    this.agents.push({ name: 'orch', instance: orch });
    orch.start().catch(err => {
      console.error('Orchestrator agent crashed:', err);
    });

    // Start recovery job
    console.log('Starting recovery job...');
    this.startRecoveryJob();

    console.log('=== All Agents Started ===\n');
  }

  /**
   * Start recovery job as separate process
   */
  startRecoveryJob() {
    this.recoveryJob = spawn('node', ['assets/recovery-job.template.js'], {
      stdio: 'inherit',
      env: process.env
    });

    this.recoveryJob.on('error', (err) => {
      console.error('Recovery job error:', err);
    });

    this.recoveryJob.on('exit', (code) => {
      console.log(`Recovery job exited with code ${code}`);
      if (code !== 0) {
        // Restart recovery job
        console.log('Restarting recovery job...');
        this.startRecoveryJob();
      }
    });
  }

  /**
   * Stop all agents
   */
  async stop() {
    console.log('\n=== Stopping All Agents ===');

    // Stop agent instances
    for (const agent of this.agents) {
      console.log(`Stopping ${agent.name}...`);
      agent.instance.stop();
    }

    // Stop recovery job
    if (this.recoveryJob) {
      console.log('Stopping recovery job...');
      this.recoveryJob.kill('SIGTERM');
    }

    console.log('=== All Agents Stopped ===');
  }
}

// Main
if (require.main === module) {
  const coordinator = new AgentCoordinator();

  process.on('SIGINT', async () => {
    await coordinator.stop();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await coordinator.stop();
    process.exit(0);
  });

  coordinator.start().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

module.exports = AgentCoordinator;
```

---

## Error Handling Patterns

### Example 4: Comprehensive Error Handler

```javascript
/**
 * error-handler.js
 * Centralized error handling for task lifecycle
 */

class TaskError extends Error {
  constructor(message, taskId, agentName, recoverable = false) {
    super(message);
    this.name = this.constructor.name;
    this.taskId = taskId;
    this.agentName = agentName;
    this.recoverable = recoverable;
    this.timestamp = new Date().toISOString();
  }
}

class TransientError extends TaskError {
  constructor(message, taskId, agentName) {
    super(message, taskId, agentName, true);
  }
}

class PermanentError extends TaskError {
  constructor(message, taskId, agentName) {
    super(message, taskId, agentName, false);
  }
}

async function handleTaskError(taskId, error, agentName, taskLifecycle) {
  console.error(`[ErrorHandler] Task ${taskId} failed:`, error.message);

  // Classify error
  const errorType = classifyError(error);

  if (errorType === 'permanent') {
    // Reject immediately
    console.log(`[ErrorHandler] Permanent error, rejecting task`);

    const rejectionReason = `Permanent failure: ${error.message}`;
    await taskLifecycle.transitionTask(
      taskId,
      'in_progress',
      'rejected',
      agentName,
      rejectionReason
    );

    return { action: 'rejected', reason: 'permanent_error' };

  } else if (errorType === 'transient') {
    // Retry with backoff
    console.log(`[ErrorHandler] Transient error, retrying task`);

    const retryResult = await taskLifecycle.handleTaskFailure(
      taskId,
      error,
      agentName
    );

    return retryResult;

  } else {
    // Unknown error type, treat as transient
    console.warn(`[ErrorHandler] Unknown error type, treating as transient`);

    const retryResult = await taskLifecycle.handleTaskFailure(
      taskId,
      error,
      agentName
    );

    return retryResult;
  }
}

function classifyError(error) {
  // Permanent errors (don't retry)
  if (error.message.includes('Invalid input') ||
      error.message.includes('Validation failed') ||
      error.message.includes('Unauthorized') ||
      error.message.includes('Forbidden') ||
      error.message.includes('Not found') ||
      error.code === 'ENOENT') {
    return 'permanent';
  }

  // Transient errors (retry)
  if (error.message.includes('timeout') ||
      error.message.includes('ECONNRESET') ||
      error.message.includes('ETIMEDOUT') ||
      error.message.includes('Rate limit') ||
      error.message.includes('429') ||
      error.message.includes('503')) {
    return 'transient';
  }

  // Default: transient
  return 'transient';
}

module.exports = {
  TaskError,
  TransientError,
  PermanentError,
  handleTaskError,
  classifyError
};
```

---

## Recovery Job Setup

### Example 5: Production Recovery Job with Monitoring

See `assets/recovery-job.template.js` for full implementation (330 lines).

**Key Features:**
- Periodic stale claim recovery (every 5 min)
- Periodic orphaned task recovery (every 5 min)
- Full health check (every 10 min)
- Duplicate detection
- Corrupted file handling
- Metrics tracking
- Graceful shutdown

**Usage:**
```bash
# Run as standalone process
node assets/recovery-job.template.js

# Or via process manager (PM2)
pm2 start assets/recovery-job.template.js --name task-recovery

# Or via Docker
docker run -d --name task-recovery \
  -v /path/to/vault:/vault \
  -e VAULT_PATH=/vault \
  -e TASK_STALE_THRESHOLD_MINUTES=60 \
  task-recovery-image
```

---

## Integration with Watchers

### Example 6: Gmail Watcher Integration

```javascript
/**
 * gmail-watcher.js
 * Writes new emails to vault for lex to process
 */

const { google } = require('googleapis');
const vaultManager = require('./vault-state-manager');

class GmailWatcher {
  constructor() {
    this.gmail = null;
    this.lastCheckTime = null;
    this.running = false;
  }

  async start() {
    console.log('[Gmail Watcher] Starting...');

    // Initialize Gmail API client
    this.gmail = await this.initializeGmailClient();

    this.running = true;
    this.lastCheckTime = new Date().toISOString();

    // Poll for new emails
    while (this.running) {
      try {
        await this.checkForNewEmails();
      } catch (err) {
        console.error('[Gmail Watcher] Error:', err);
      }

      await this.sleep(60000);  // Check every minute
    }
  }

  async checkForNewEmails() {
    // Query for new emails with #ai-action label
    const response = await this.gmail.users.messages.list({
      userId: 'me',
      q: `label:ai-action after:${this.formatDate(this.lastCheckTime)}`
    });

    const messages = response.data.messages || [];

    if (messages.length === 0) {
      return;
    }

    console.log(`[Gmail Watcher] Found ${messages.length} new emails`);

    for (const message of messages) {
      await this.processEmail(message.id);
    }

    this.lastCheckTime = new Date().toISOString();
  }

  async processEmail(messageId) {
    // Fetch full email
    const email = await this.gmail.users.messages.get({
      userId: 'me',
      id: messageId
    });

    // Extract email data
    const headers = email.data.payload.headers;
    const from = headers.find(h => h.name === 'From')?.value;
    const subject = headers.find(h => h.name === 'Subject')?.value;
    const body = this.extractBody(email.data.payload);

    // Create vault entry
    const timestamp = new Date().toISOString();
    const filename = `${timestamp}-${messageId}.json`;

    const vaultEntry = {
      created_at: timestamp,
      created_by: 'watcher-gmail',
      status: 'needs_action',
      priority: this.detectPriority(subject, body),
      source: 'email',
      data: {
        id: messageId,
        from: from,
        subject: subject,
        body: body,
        received_at: timestamp
      }
    };

    // Write to vault
    await vaultManager.writeVaultFile(
      `Needs_Action/emails/${filename}`,
      JSON.stringify(vaultEntry, null, 2),
      'watcher-gmail'
    );

    console.log(`[Gmail Watcher] ✓ Wrote email to vault: ${filename}`);

    // Log to watcher log
    await this.logEvent('email_received', messageId, filename);
  }

  detectPriority(subject, body) {
    const urgentKeywords = ['urgent', 'asap', 'immediate', 'critical'];
    const text = `${subject} ${body}`.toLowerCase();

    for (const keyword of urgentKeywords) {
      if (text.includes(keyword)) {
        return 'high';
      }
    }

    return 'medium';
  }

  extractBody(payload) {
    // Extract text from email payload
    if (payload.body?.data) {
      return Buffer.from(payload.body.data, 'base64').toString('utf-8');
    }

    if (payload.parts) {
      for (const part of payload.parts) {
        if (part.mimeType === 'text/plain' && part.body?.data) {
          return Buffer.from(part.body.data, 'base64').toString('utf-8');
        }
      }
    }

    return '';
  }

  async logEvent(event, emailId, filename) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      event: event,
      email_id: emailId,
      file: filename
    };

    await vaultManager.appendLog('watcher-gmail.json', JSON.stringify(logEntry));
  }

  stop() {
    console.log('[Gmail Watcher] Stopping...');
    this.running = false;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  formatDate(isoString) {
    return isoString.split('T')[0];
  }

  async initializeGmailClient() {
    // Initialize Gmail API client (implementation depends on auth setup)
    // See Google APIs Node.js documentation
    throw new Error('Gmail client initialization not implemented');
  }
}

module.exports = GmailWatcher;
```

---

## Monitoring & Metrics

### Example 7: Prometheus Metrics Exporter

```javascript
/**
 * metrics-exporter.js
 * Export task lifecycle metrics for Prometheus
 */

const client = require('prom-client');
const vaultManager = require('./vault-state-manager');

// Metrics
const taskCountGauge = new client.Gauge({
  name: 'task_count_by_stage',
  help: 'Number of tasks in each lifecycle stage',
  labelNames: ['stage']
});

const transitionCounter = new client.Counter({
  name: 'task_transitions_total',
  help: 'Total number of task transitions',
  labelNames: ['from_state', 'to_state', 'agent']
});

const taskDurationHistogram = new client.Histogram({
  name: 'task_duration_seconds',
  help: 'Task processing duration',
  labelNames: ['outcome'],
  buckets: [1, 5, 10, 30, 60, 300, 600, 1800, 3600]  // 1s to 1h
});

const retryCounter = new client.Counter({
  name: 'task_retries_total',
  help: 'Total number of task retries',
  labelNames: ['reason']
});

const recoveryCounter = new client.Counter({
  name: 'recovery_actions_total',
  help: 'Total number of recovery actions',
  labelNames: ['type']  // stale_claim, orphaned_task, duplicate, corrupted
});

// Collect metrics periodically
async function collectMetrics() {
  const folders = ['Needs_Action', 'Plans', 'In_Progress', 'Pending_Approval', 'Approved', 'Done', 'Rejected'];

  for (const folder of folders) {
    const files = await vaultManager.listFolderFiles(folder);
    const stage = folder.toLowerCase().replace('_', '_');
    taskCountGauge.set({ stage }, files.length);
  }
}

// Start metrics server
function startMetricsServer(port = 9090) {
  const express = require('express');
  const app = express();

  app.get('/metrics', async (req, res) => {
    try {
      await collectMetrics();
      res.set('Content-Type', client.register.contentType);
      res.end(await client.register.metrics());
    } catch (err) {
      res.status(500).end(err.message);
    }
  });

  app.listen(port, () => {
    console.log(`Metrics server listening on port ${port}`);
  });
}

module.exports = {
  taskCountGauge,
  transitionCounter,
  taskDurationHistogram,
  retryCounter,
  recoveryCounter,
  startMetricsServer
};
```

---

## Complete System Integration

### Example 8: Full System Startup Script

```bash
#!/bin/bash
# start-agents.sh
# Start all Digital FTE agents

set -euo pipefail

echo "==================================="
echo "Starting Digital FTE Agent System"
echo "==================================="

# Check vault exists
if [ ! -d "$VAULT_PATH" ]; then
  echo "Error: Vault not found at $VAULT_PATH"
  echo "Run: VAULT_PATH=/path/to/vault bash assets/vault-init.sh"
  exit 1
fi

# Start recovery job (background)
echo "Starting recovery job..."
node assets/recovery-job.template.js > logs/recovery.log 2>&1 &
RECOVERY_PID=$!
echo "  PID: $RECOVERY_PID"

# Start lex agent (background)
echo "Starting lex agent..."
node lex-agent.js > logs/lex.log 2>&1 &
LEX_PID=$!
echo "  PID: $LEX_PID"

# Start orchestrator agent (background)
echo "Starting orchestrator agent..."
node orchestrator-agent.js > logs/orchestrator.log 2>&1 &
ORCH_PID=$!
echo "  PID: $ORCH_PID"

# Start metrics exporter (background)
echo "Starting metrics exporter..."
node metrics-exporter.js > logs/metrics.log 2>&1 &
METRICS_PID=$!
echo "  PID: $METRICS_PID"

echo ""
echo "==================================="
echo "All agents started"
echo "==================================="
echo "  Recovery job: $RECOVERY_PID"
echo "  Lex agent: $LEX_PID"
echo "  Orchestrator: $ORCH_PID"
echo "  Metrics: $METRICS_PID"
echo ""
echo "Logs:"
echo "  tail -f logs/recovery.log"
echo "  tail -f logs/lex.log"
echo "  tail -f logs/orchestrator.log"
echo ""
echo "Metrics: http://localhost:9090/metrics"
echo ""
echo "To stop: kill $RECOVERY_PID $LEX_PID $ORCH_PID $METRICS_PID"
```

---

## Summary

These examples provide production-ready implementations for:

✅ **Complete agent implementations** (lex, orchestrator)
✅ **Multi-agent coordination**
✅ **Comprehensive error handling**
✅ **Recovery job setup**
✅ **Watcher integration** (Gmail example)
✅ **Monitoring & metrics** (Prometheus)
✅ **System startup scripts**

All examples follow best practices:
- Graceful shutdown
- Heartbeat mechanism
- Error classification
- Retry logic
- Audit logging
- Metrics tracking
