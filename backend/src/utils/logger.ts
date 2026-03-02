/**
 * Structured Logging Utility
 * Provides JSON-formatted logging for production and pretty logging for development
 */

import config from '../config/env';

type LogLevel = 'error' | 'warn' | 'info' | 'debug';

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  [key: string]: unknown;
}

class Logger {
  private level: LogLevel;
  private levelPriority: Record<LogLevel, number> = {
    error: 0,
    warn: 1,
    info: 2,
    debug: 3,
  };

  constructor(level: LogLevel = 'info') {
    this.level = level;
  }

  private shouldLog(level: LogLevel): boolean {
    return this.levelPriority[level] <= this.levelPriority[this.level];
  }

  private formatEntry(entry: LogEntry): string {
    if (config.NODE_ENV === 'production') {
      return JSON.stringify(entry);
    }
    const timestamp = new Date(entry.timestamp).toISOString();
    const levelPad = entry.level.toUpperCase().padEnd(5);
    return `[${timestamp}] ${levelPad} ${entry.message}`;
  }

  private log(level: LogLevel, message: string, meta?: Record<string, unknown>) {
    if (!this.shouldLog(level)) return;

    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      ...meta,
    };

    const output = this.formatEntry(entry);

    switch (level) {
      case 'error':
        console.error(output);
        break;
      case 'warn':
        console.warn(output);
        break;
      default:
        console.log(output);
    }
  }

  error(message: string, meta?: Record<string, unknown>) {
    this.log('error', message, meta);
  }

  warn(message: string, meta?: Record<string, unknown>) {
    this.log('warn', message, meta);
  }

  info(message: string, meta?: Record<string, unknown>) {
    this.log('info', message, meta);
  }

  debug(message: string, meta?: Record<string, unknown>) {
    this.log('debug', message, meta);
  }
}

// Export singleton instance
export const logger = new Logger(config.LOG_LEVEL);

export default logger;
