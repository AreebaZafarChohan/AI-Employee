/**
 * Environment Configuration Loader
 * Validates all environment variables using Zod schema
 */

import * as dotenv from 'dotenv';
import { z } from 'zod';

dotenv.config();

// Define environment schema
const EnvSchema = z.object({
  // Database - optional for tests
  DATABASE_URL: z.string().optional().default('file:./dev.db'),

  // AI Provider
  AI_PROVIDER: z.enum(['anthropic', 'openai', 'google', 'mock']).default('mock'),
  AI_API_KEY: z.string().min(1).optional().or(z.literal('')),

  // Server
  NODE_ENV: z.enum(['development', 'production', 'test']).default('test'),
  PORT: z.string().transform((val) => parseInt(val, 10)).default('3000'),
  HOST: z.string().default('0.0.0.0'),

  // CORS
  CORS_ORIGIN: z.string().default('*'),
  CORS_METHODS: z.string().default('GET,POST,PUT,PATCH,DELETE'),
  CORS_HEADERS: z.string().default('Content-Type,Authorization'),

  // Logging - case insensitive
  LOG_LEVEL: z.string().toLowerCase().transform((val) => {
    if (['error', 'warn', 'info', 'debug'].includes(val)) return val as 'error' | 'warn' | 'info' | 'debug';
    return 'info';
  }).default('info'),

  // External APIs & Vault
  GEMINI_API_KEY: z.string().optional(),
  GROK_API_KEY: z.string().optional(),
  TWITTER_API_KEY: z.string().optional(),
  TWITTER_API_SECRET: z.string().optional(),
  TWITTER_ACCESS_TOKEN: z.string().optional(),
  TWITTER_ACCESS_TOKEN_SECRET: z.string().optional(),
  VAULT_PATH: z.string().optional(),
});

export type Env = z.infer<typeof EnvSchema>;

// Load and validate environment
function loadEnv(): Env {
  const result = EnvSchema.safeParse(process.env);

  if (!result.success) {
    console.error('❌ Environment validation failed:');
    result.error.errors.forEach((err) => {
      console.error(`  - ${err.path.join('.')}: ${err.message}`);
    });
    process.exit(1);
  }

  return result.data;
}

// Export validated config
export const config = loadEnv();

export default config;
