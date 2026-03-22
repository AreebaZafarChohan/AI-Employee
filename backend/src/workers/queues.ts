import { Queue } from 'bullmq';
import IORedis from 'ioredis';
import dotenv from 'dotenv';

dotenv.config();

const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
const connection = new IORedis(redisUrl, {
  maxRetriesPerRequest: null,
});

export const decompositionQueue = new Queue('decomposition', {
  connection: connection as any,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 1000,
    },
    removeOnComplete: true,
  },
});

export const executionQueue = new Queue('execution', {
  connection: connection as any,
  defaultJobOptions: {
    attempts: 5,
    backoff: {
      type: 'exponential',
      delay: 2000,
    },
    removeOnComplete: false, // Keep records for auditing
  },
});

export const memoryQueue = new Queue('memory', {
  connection: connection as any,
  defaultJobOptions: {
    removeOnComplete: true,
  },
});

console.log('BullMQ queues initialized');
