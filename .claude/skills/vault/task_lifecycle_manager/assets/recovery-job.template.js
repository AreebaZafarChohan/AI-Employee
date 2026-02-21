#!/usr/bin/env node
/**
 * Task Lifecycle Recovery Job
 *
 * Runs periodic recovery tasks to detect and fix:
 * - Stale claims (tasks stuck in Plans/)
 * - Orphaned tasks (tasks stuck in In_Progress/)
 * - Duplicate tasks
 * - Corrupted files
 */

const taskLifecycle = require('./task-lifecycle-manager');
const vaultManager = require('./vault-state-manager');

// Configuration
const CONFIG = {
  staleThresholdMinutes: parseInt(process.env.TASK_STALE_THRESHOLD_MINUTES || '60'),
  orphanThresholdMinutes: parseInt(process.env.TASK_ORPHAN_THRESHOLD_MINUTES || '30'),
  recoveryIntervalMs: parseInt(process.env.TASK_RECOVERY_INTERVAL_MS || '300000'),  // 5 min
  healthCheckIntervalMs: parseInt(process.env.TASK_HEALTH_CHECK_INTERVAL_MS || '600000')  // 10 min
};

// Metrics
const metrics = {
  staleClaimsRecovered: 0,
  orphanedTasksRecovered: 0,
  duplicatesResolved: 0,
  corruptedFilesHandled: 0,
  lastRecoveryRun: null,
  lastHealthCheckRun: null
};

/**
 * Recover stale claims (tasks stuck in Plans/)
 */
async function recoverStaleClaims() {
  console.log('[Recovery] Checking for stale claims...');

  const staleTime = Date.now() - (CONFIG.staleThresholdMinutes * 60 * 1000);
  const plansFiles = await vaultManager.listFolderFiles('Plans');

  let recovered = 0;

  for (const file of plansFiles) {
    if (file.created.getTime() < staleTime) {
      try {
        // Read task
        const { content } = await vaultManager.readVaultFile(`Plans/${file.name}`, 'system');
        const task = JSON.parse(content);

        console.log(`[Recovery] Stale claim detected: ${file.name} (claimed ${Math.floor((Date.now() - file.created.getTime()) / 60000)} min ago)`);

        // Reset status
        task.status = 'needs_action';
        task.stale_recovery = {
          recovered_at: new Date().toISOString(),
          was_claimed_by: task.claimed_by || 'unknown',
          was_claimed_at: task.claimed_at || file.created.toISOString(),
          stale_duration_minutes: Math.floor((Date.now() - file.created.getTime()) / 60000)
        };

        delete task.claimed_by;
        delete task.claimed_at;

        // Write back
        await vaultManager.writeVaultFile(
          `Plans/${file.name}`,
          JSON.stringify(task, null, 2),
          'system'
        );

        // Move to Needs_Action
        await vaultManager.moveFile('Plans', file.name, 'Needs_Action', 'system');

        recovered++;
        metrics.staleClaimsRecovered++;

      } catch (err) {
        console.error(`[Recovery] Failed to recover stale claim ${file.name}:`, err.message);
      }
    }
  }

  if (recovered > 0) {
    console.log(`[Recovery] ✓ Recovered ${recovered} stale claims`);
  } else {
    console.log('[Recovery] No stale claims found');
  }

  return recovered;
}

/**
 * Recover orphaned tasks (tasks stuck in In_Progress/)
 */
async function recoverOrphanedTasks() {
  console.log('[Recovery] Checking for orphaned tasks...');

  const orphanTime = Date.now() - (CONFIG.orphanThresholdMinutes * 60 * 1000);
  const inProgressFiles = await vaultManager.listFolderFiles('In_Progress');

  let recovered = 0;

  for (const file of inProgressFiles) {
    try {
      // Read task
      const { content } = await vaultManager.readVaultFile(`In_Progress/${file.name}`, 'system');
      const task = JSON.parse(content);

      // Check heartbeat (if exists)
      const lastHeartbeat = task.last_heartbeat
        ? new Date(task.last_heartbeat).getTime()
        : file.modified.getTime();

      if (lastHeartbeat < orphanTime) {
        console.log(`[Recovery] Orphaned task detected: ${file.name} (last update ${Math.floor((Date.now() - lastHeartbeat) / 60000)} min ago)`);

        // Reset status
        task.status = 'needs_action';
        task.orphan_recovery = {
          recovered_at: new Date().toISOString(),
          was_owned_by: task.claimed_by || 'unknown',
          last_heartbeat: task.last_heartbeat || file.modified.toISOString(),
          orphan_duration_minutes: Math.floor((Date.now() - lastHeartbeat) / 60000),
          reason: 'no_heartbeat_timeout'
        };

        // Write back
        await vaultManager.writeVaultFile(
          `In_Progress/${file.name}`,
          JSON.stringify(task, null, 2),
          'system'
        );

        // Move to Needs_Action
        await vaultManager.moveFile('In_Progress', file.name, 'Needs_Action', 'system');

        recovered++;
        metrics.orphanedTasksRecovered++;
      }

    } catch (err) {
      console.error(`[Recovery] Failed to recover orphaned task ${file.name}:`, err.message);
    }
  }

  if (recovered > 0) {
    console.log(`[Recovery] ✓ Recovered ${recovered} orphaned tasks`);
  } else {
    console.log('[Recovery] No orphaned tasks found');
  }

  return recovered;
}

/**
 * Detect and resolve duplicate tasks
 */
async function detectDuplicateTasks() {
  console.log('[Recovery] Checking for duplicate tasks...');

  const allTasks = {};
  const duplicates = [];

  const folders = ['Needs_Action', 'Plans', 'In_Progress', 'Pending_Approval', 'Approved', 'Done'];

  for (const folder of folders) {
    const files = await vaultManager.listFolderFiles(folder);

    for (const file of files) {
      try {
        const { content } = await vaultManager.readVaultFile(`${folder}/${file.name}`, 'system');
        const task = JSON.parse(content);

        if (allTasks[task.plan_id]) {
          // Duplicate found!
          duplicates.push({
            taskId: task.plan_id,
            locations: [allTasks[task.plan_id], `${folder}/${file.name}`]
          });
        } else {
          allTasks[task.plan_id] = `${folder}/${file.name}`;
        }
      } catch (err) {
        // Ignore parse errors (handled by corrupted file check)
      }
    }
  }

  if (duplicates.length > 0) {
    console.log(`[Recovery] Found ${duplicates.length} duplicate tasks`);

    for (const dup of duplicates) {
      // Keep first location (oldest), reject rest
      const toKeep = dup.locations[0];
      const toReject = dup.locations.slice(1);

      console.log(`[Recovery] Keeping: ${toKeep}`);

      for (const loc of toReject) {
        const [folder, filename] = loc.split('/');

        try {
          // Move to Rejected
          await vaultManager.moveFile(folder, filename, 'Rejected', 'system');

          // Add rejection reason
          const rejectionPath = `Rejected/${filename.replace('.json', '.rejection.md')}`;
          await vaultManager.writeVaultFile(
            rejectionPath,
            `# Duplicate Task\n\nThis task is a duplicate of ${toKeep}.\n\nResolved by recovery job at ${new Date().toISOString()}`,
            'system'
          );

          console.log(`[Recovery] Rejected duplicate: ${loc}`);
          metrics.duplicatesResolved++;

        } catch (err) {
          console.error(`[Recovery] Failed to reject duplicate ${loc}:`, err.message);
        }
      }
    }
  } else {
    console.log('[Recovery] No duplicate tasks found');
  }

  return duplicates.length;
}

/**
 * Detect and handle corrupted files
 */
async function detectCorruptedFiles() {
  console.log('[Recovery] Checking for corrupted files...');

  const folders = ['Needs_Action', 'Plans', 'In_Progress', 'Pending_Approval', 'Approved', 'Done'];
  let corrupted = 0;

  for (const folder of folders) {
    const files = await vaultManager.listFolderFiles(folder);

    for (const file of files) {
      try {
        const { content } = await vaultManager.readVaultFile(`${folder}/${file.name}`, 'system');
        JSON.parse(content);  // Validate JSON
      } catch (err) {
        console.log(`[Recovery] Corrupted file detected: ${folder}/${file.name}`);

        try {
          // Move to Rejected
          await vaultManager.moveFile(folder, file.name, 'Rejected', 'system');

          // Add rejection reason
          const rejectionPath = `Rejected/${file.name.replace('.json', '.rejection.md')}`;
          await vaultManager.writeVaultFile(
            rejectionPath,
            `# Corrupted File\n\nFile corrupted (invalid JSON): ${err.message}\n\nMoved by recovery job at ${new Date().toISOString()}`,
            'system'
          );

          corrupted++;
          metrics.corruptedFilesHandled++;

        } catch (moveErr) {
          console.error(`[Recovery] Failed to move corrupted file ${file.name}:`, moveErr.message);
        }
      }
    }
  }

  if (corrupted > 0) {
    console.log(`[Recovery] ✓ Handled ${corrupted} corrupted files`);
  } else {
    console.log('[Recovery] No corrupted files found');
  }

  return corrupted;
}

/**
 * Run all recovery tasks
 */
async function runRecoveryJobs() {
  console.log('=== Running Recovery Jobs ===');
  const startTime = Date.now();

  try {
    await recoverStaleClaims();
    await recoverOrphanedTasks();

    metrics.lastRecoveryRun = new Date().toISOString();
    const duration = Date.now() - startTime;
    console.log(`=== Recovery Jobs Complete (${duration}ms) ===\n`);

  } catch (err) {
    console.error('[Recovery] Recovery jobs failed:', err);
  }
}

/**
 * Run full health check (includes duplicate detection and corruption check)
 */
async function runHealthCheck() {
  console.log('=== Running Health Check ===');
  const startTime = Date.now();

  try {
    await recoverStaleClaims();
    await recoverOrphanedTasks();
    await detectDuplicateTasks();
    await detectCorruptedFiles();

    metrics.lastHealthCheckRun = new Date().toISOString();
    const duration = Date.now() - startTime;

    console.log('=== Health Check Complete ===');
    console.log(`  Duration: ${duration}ms`);
    console.log(`  Stale claims recovered: ${metrics.staleClaimsRecovered}`);
    console.log(`  Orphaned tasks recovered: ${metrics.orphanedTasksRecovered}`);
    console.log(`  Duplicates resolved: ${metrics.duplicatesResolved}`);
    console.log(`  Corrupted files handled: ${metrics.corruptedFilesHandled}`);
    console.log('');

  } catch (err) {
    console.error('[Health Check] Health check failed:', err);
  }
}

/**
 * Main loop
 */
async function main() {
  console.log('Task Lifecycle Recovery Job started');
  console.log(`  Stale threshold: ${CONFIG.staleThresholdMinutes} minutes`);
  console.log(`  Orphan threshold: ${CONFIG.orphanThresholdMinutes} minutes`);
  console.log(`  Recovery interval: ${CONFIG.recoveryIntervalMs / 1000} seconds`);
  console.log(`  Health check interval: ${CONFIG.healthCheckIntervalMs / 1000} seconds`);
  console.log('');

  // Run recovery jobs periodically
  setInterval(async () => {
    try {
      await runRecoveryJobs();
    } catch (err) {
      console.error('[Main] Recovery job error:', err);
    }
  }, CONFIG.recoveryIntervalMs);

  // Run full health check periodically
  setInterval(async () => {
    try {
      await runHealthCheck();
    } catch (err) {
      console.error('[Main] Health check error:', err);
    }
  }, CONFIG.healthCheckIntervalMs);

  // Run immediately on startup
  await runHealthCheck();
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\nGracefully shutting down...');
  console.log('Final metrics:', metrics);
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\nReceived SIGTERM, shutting down...');
  console.log('Final metrics:', metrics);
  process.exit(0);
});

// Start
main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
