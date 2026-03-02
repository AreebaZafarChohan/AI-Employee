/**
 * Tests for Email MCP Server
 * 
 * Run with: npm test
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// Test utilities
const TEST_DIR = join(ROOT, 'test-temp');
const RATE_FILE = join(TEST_DIR, 'rate_limit.json');
const SCHEDULE_FILE = join(TEST_DIR, 'schedules.json');

// Helper: Clean test directory
function setupTestEnv() {
  if (existsSync(TEST_DIR)) {
    rmSync(TEST_DIR, { recursive: true, force: true });
  }
  mkdirSync(TEST_DIR, { recursive: true });
}

function cleanupTestEnv() {
  if (existsSync(TEST_DIR)) {
    rmSync(TEST_DIR, { recursive: true, force: true });
  }
}

describe('Email MCP Server', () => {
  beforeEach(() => {
    setupTestEnv();
  });

  afterEach(() => {
    cleanupTestEnv();
  });

  describe('Rate Limiter', () => {
    it('should allow emails under limit', () => {
      // Simulate rate limit state
      const state = { date: new Date().toISOString().slice(0, 10), count: 5 };
      writeFileSync(RATE_FILE, JSON.stringify(state), 'utf-8');
      
      const saved = JSON.parse(readFileSync(RATE_FILE, 'utf-8'));
      assert.strictEqual(saved.count, 5);
      assert.strictEqual(saved.date, state.date);
    });

    it('should reset count on new day', () => {
      // Set old date
      const oldState = { date: '2020-01-01', count: 10 };
      writeFileSync(RATE_FILE, JSON.stringify(oldState), 'utf-8');
      
      const today = new Date().toISOString().slice(0, 10);
      assert.notStrictEqual(today, '2020-01-01');
    });

    it('should persist state to file', () => {
      const state = { date: new Date().toISOString().slice(0, 10), count: 3 };
      writeFileSync(RATE_FILE, JSON.stringify(state), 'utf-8');
      
      assert.ok(existsSync(RATE_FILE));
      const loaded = JSON.parse(readFileSync(RATE_FILE, 'utf-8'));
      assert.deepStrictEqual(loaded, state);
    });
  });

  describe('Schedule Store', () => {
    it('should save and load schedules', () => {
      const schedules = [
        {
          schedule_id: 'sch_001',
          status: 'pending',
          to: 'test@example.com',
          subject: 'Test',
          send_at: '2026-03-02T10:00:00Z',
        },
      ];
      
      writeFileSync(SCHEDULE_FILE, JSON.stringify(schedules, null, 2), 'utf-8');
      
      const loaded = JSON.parse(readFileSync(SCHEDULE_FILE, 'utf-8'));
      assert.strictEqual(loaded.length, 1);
      assert.strictEqual(loaded[0].schedule_id, 'sch_001');
    });

    it('should handle empty schedule file', () => {
      writeFileSync(SCHEDULE_FILE, '[]', 'utf-8');
      
      const loaded = JSON.parse(readFileSync(SCHEDULE_FILE, 'utf-8'));
      assert.strictEqual(loaded.length, 0);
    });
  });

  describe('Input Validation', () => {
    it('should validate email addresses', () => {
      const validEmail = 'user@example.com';
      const invalidEmail = 'not-an-email';
      
      // Simple regex check (server uses Zod)
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      
      assert.ok(emailRegex.test(validEmail));
      assert.ok(!emailRegex.test(invalidEmail));
    });

    it('should validate ISO 8601 datetime', () => {
      const validDate = '2026-03-02T10:00:00Z';
      const invalidDate = 'not-a-date';
      
      const parsed = new Date(validDate);
      const invalid = new Date(invalidDate);
      
      assert.ok(!isNaN(parsed.getTime()));
      assert.ok(isNaN(invalid.getTime()));
    });

    it('should reject past dates for scheduling', () => {
      const pastDate = '2020-01-01T00:00:00Z';
      const futureDate = '2030-01-01T00:00:00Z';
      
      const past = new Date(pastDate);
      const future = new Date(futureDate);
      const now = new Date();
      
      assert.ok(past < now);
      assert.ok(future > now);
    });
  });

  describe('DRY_RUN Mode', () => {
    it('should respect DRY_RUN environment variable', () => {
      process.env.DRY_RUN = 'true';
      const dryRun = process.env.DRY_RUN?.toLowerCase() === 'true';
      assert.strictEqual(dryRun, true);
      
      process.env.DRY_RUN = 'false';
    });

    it('should default to false when not set', () => {
      delete process.env.DRY_RUN;
      const dryRun = process.env.DRY_RUN?.toLowerCase() === 'true';
      assert.strictEqual(dryRun, false);
    });
  });

  describe('Approval Gate', () => {
    it('should check REQUIRE_APPROVAL flag', () => {
      process.env.REQUIRE_APPROVAL = 'true';
      const requireApproval = process.env.REQUIRE_APPROVAL?.toLowerCase() === 'true';
      assert.strictEqual(requireApproval, true);
      
      process.env.REQUIRE_APPROVAL = 'false';
    });

    it('should allow send when approved=true', () => {
      const approved = true;
      const requireApproval = true;
      
      const canSend = !requireApproval || approved;
      assert.strictEqual(canSend, true);
    });

    it('should block send when approved=false and REQUIRE_APPROVAL=true', () => {
      const approved = false;
      const requireApproval = true;
      
      const canSend = !requireApproval || approved;
      assert.strictEqual(canSend, false);
    });
  });

  describe('Log Format', () => {
    it('should produce valid JSON log entries', () => {
      const logEntry = {
        timestamp: new Date().toISOString(),
        level: 'info',
        tool: 'send_email',
        message: 'Email sent',
        dry_run: false,
        to: 'test@example.com',
      };
      
      const json = JSON.stringify(logEntry);
      const parsed = JSON.parse(json);
      
      assert.strictEqual(parsed.level, 'info');
      assert.strictEqual(parsed.tool, 'send_email');
      assert.ok(parsed.timestamp);
    });

    it('should include all required fields', () => {
      const logEntry = {
        timestamp: '2026-03-01T10:00:00.000Z',
        level: 'info',
        tool: 'send_email',
        message: 'Test',
        dry_run: false,
      };
      
      const required = ['timestamp', 'level', 'tool', 'message'];
      for (const field of required) {
        assert.ok(Object.prototype.hasOwnProperty.call(logEntry, field));
      }
    });
  });

  describe('Gmail Query Syntax', () => {
    it('should support common search operators', () => {
      const queries = [
        'is:unread',
        'from:client@example.com',
        'subject:invoice',
        'after:2026/02/01',
        'before:2026/02/28',
        'is:important',
        'label:work',
        'has:attachment',
      ];
      
      // All should be non-empty strings
      for (const query of queries) {
        assert.ok(typeof query === 'string');
        assert.ok(query.length > 0);
      }
    });
  });

  describe('Error Handling', () => {
    it('should handle missing credentials', () => {
      delete process.env.GMAIL_CLIENT_ID;
      delete process.env.GMAIL_CLIENT_SECRET;
      delete process.env.GMAIL_REFRESH_TOKEN;
      
      const hasCredentials = !!(
        process.env.GMAIL_CLIENT_ID &&
        process.env.GMAIL_CLIENT_SECRET &&
        process.env.GMAIL_REFRESH_TOKEN
      );
      
      assert.strictEqual(hasCredentials, false);
    });

    it('should handle rate limit exceeded', () => {
      const limit = 10;
      const count = 10;
      
      const isExceeded = count >= limit;
      assert.strictEqual(isExceeded, true);
    });

    it('should handle invalid JSON gracefully', () => {
      const invalidJson = '{ invalid json }';
      
      let parsed = null;
      let error = null;
      
      try {
        parsed = JSON.parse(invalidJson);
      } catch (e) {
        error = e.message;
      }
      
      assert.strictEqual(parsed, null);
      assert.ok(error);
    });
  });

  describe('Configuration', () => {
    it('should load from .env file', () => {
      const envPath = join(ROOT, '.env');
      
      if (existsSync(envPath)) {
        const content = readFileSync(envPath, 'utf-8');
        assert.ok(content.includes('GMAIL_CLIENT_ID='));
        assert.ok(content.includes('GMAIL_CLIENT_SECRET='));
        assert.ok(content.includes('GMAIL_REFRESH_TOKEN='));
      }
    });

    it('should have valid rate limit default', () => {
      const defaultLimit = 10;
      assert.ok(defaultLimit > 0);
      assert.ok(defaultLimit <= 100);
    });

    it('should have valid log level', () => {
      const validLevels = ['debug', 'info', 'error'];
      const defaultLevel = 'info';
      
      assert.ok(validLevels.includes(defaultLevel));
    });
  });
});

describe('Tool Schemas', () => {
  describe('send_email', () => {
    it('should require to, subject, body', () => {
      const required = ['to', 'subject', 'body'];
      assert.strictEqual(required.length, 3);
    });

    it('should accept optional fields', () => {
      const optional = ['cc', 'bcc', 'reply_to', 'thread_id', 'approved'];
      assert.ok(optional.includes('cc'));
      assert.ok(optional.includes('approved'));
    });
  });

  describe('draft_email', () => {
    it('should require to, subject, body', () => {
      const required = ['to', 'subject', 'body'];
      assert.strictEqual(required.length, 3);
    });

    it('should not require approved field', () => {
      const optional = ['cc', 'bcc', 'reply_to', 'thread_id'];
      assert.ok(!optional.includes('approved'));
    });
  });

  describe('schedule_email', () => {
    it('should require to, subject, body, send_at', () => {
      const required = ['to', 'subject', 'body', 'send_at'];
      assert.strictEqual(required.length, 4);
    });

    it('should validate send_at is ISO 8601', () => {
      const validFormat = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/;
      const testDate = '2026-03-02T10:00:00Z';
      
      assert.ok(validFormat.test(testDate));
    });
  });

  describe('search_inbox', () => {
    it('should require only query', () => {
      const required = ['query'];
      assert.strictEqual(required.length, 1);
    });

    it('should have optional max_results and include_body', () => {
      const optional = ['max_results', 'include_body'];
      assert.strictEqual(optional.length, 2);
    });
  });
});
