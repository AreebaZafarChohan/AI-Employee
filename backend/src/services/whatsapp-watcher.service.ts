/**
 * WhatsApp Watcher Service
 * Spawns the Python WhatsApp watcher as a child process with auto-restart.
 */

import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import logger from '../utils/logger';

const ROOT_PATH = path.resolve(__dirname, '..', '..', '..');
const WATCHER_SCRIPT = path.join(ROOT_PATH, 'src', 'watcher', 'whatsapp_watcher.py');
const VAULT_PATH = process.env.VAULT_PATH || path.join(ROOT_PATH, 'AI-Employee-Vault');

class WhatsAppWatcherService {
  private process: ChildProcess | null = null;
  private running = false;
  private restartAttempts = 0;
  private maxRestartAttempts = 5;
  private restartTimer: NodeJS.Timeout | null = null;

  start(): void {
    if (this.running) {
      logger.warn('WhatsApp watcher already running');
      return;
    }

    logger.info('Starting WhatsApp watcher...');
    this.running = true;
    this.spawnProcess();
  }

  stop(): void {
    this.running = false;
    if (this.restartTimer) {
      clearTimeout(this.restartTimer);
      this.restartTimer = null;
    }
    if (this.process) {
      this.process.kill('SIGTERM');
      this.process = null;
    }
    logger.info('WhatsApp watcher stopped');
  }

  isRunning(): boolean {
    return this.running && this.process !== null;
  }

  private spawnProcess(): void {
    const env = {
      ...process.env,
      DRY_RUN: 'false',
      VAULT_PATH,
      WA_HEADLESS: process.env.WA_HEADLESS || 'false',
    };

    this.process = spawn('python', [WATCHER_SCRIPT, '--watch'], {
      cwd: ROOT_PATH,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    this.process.stdout?.on('data', (data: Buffer) => {
      const msg = data.toString().trim();
      if (msg) logger.info(`[whatsapp-watcher] ${msg}`);
    });

    this.process.stderr?.on('data', (data: Buffer) => {
      const msg = data.toString().trim();
      if (msg) logger.warn(`[whatsapp-watcher] ${msg}`);
    });

    this.process.on('exit', (code) => {
      this.process = null;
      if (!this.running) return;

      logger.warn(`WhatsApp watcher exited with code ${code}`);
      this.restartAttempts++;

      if (this.restartAttempts > this.maxRestartAttempts) {
        logger.error('WhatsApp watcher exceeded max restart attempts, giving up');
        this.running = false;
        return;
      }

      const backoff = Math.min(1000 * Math.pow(2, this.restartAttempts), 30000);
      logger.info(`Restarting WhatsApp watcher in ${backoff}ms (attempt ${this.restartAttempts})`);
      this.restartTimer = setTimeout(() => this.spawnProcess(), backoff);
    });

    this.process.on('error', (err) => {
      logger.error('Failed to spawn WhatsApp watcher:', { error: err.message });
      this.process = null;
    });

    this.restartAttempts = 0;
    logger.info('WhatsApp watcher started');
  }
}

export const whatsappWatcherService = new WhatsAppWatcherService();
