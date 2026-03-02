/**
 * CORS Configuration
 * Configures Cross-Origin Resource Sharing based on environment variables
 */

import { CorsOptions } from 'cors';
import config from './env';

export function getCorsOptions(): CorsOptions {
  const origins = config.CORS_ORIGIN.split(',').map((origin) => origin.trim());

  return {
    origin: origins.includes('*') ? '*' : origins,
    methods: config.CORS_METHODS.split(',').map((m) => m.trim()),
    allowedHeaders: config.CORS_HEADERS.split(',').map((h) => h.trim()),
    credentials: true,
    optionsSuccessStatus: 200,
  };
}

export default getCorsOptions;
