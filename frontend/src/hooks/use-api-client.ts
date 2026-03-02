/**
 * Base API Client Hook
 * TanStack Query setup and configuration
 */

'use client';

import { QueryClient } from '@tanstack/react-query';
import { apiClient, ApiClientError } from '@/lib/api-client';
import type { ApiError, ErrorCode } from '@/types/api';

/**
 * Create a configured QueryClient instance
 */
export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // With SSR, we usually want to set some default staleTime
        // above 0 to avoid refetching immediately on the client
        staleTime: 1000 * 60, // 1 minute
        retry: (failureCount, error) => {
          // Don't retry on client errors (4xx)
          if (error instanceof ApiClientError) {
            return false;
          }
          // Retry on network errors or 5xx
          return failureCount < 3;
        },
      },
      mutations: {
        retry: false, // Don't retry mutations by default
      },
    },
  });
}

/**
 * Parse API error into a consistent format
 */
export function parseApiError(error: unknown): ApiError {
  if (error instanceof ApiClientError) {
    return {
      code: error.code as ErrorCode,
      message: error.message,
      details: error.details,
    };
  }
  return {
    code: 'INTERNAL_ERROR' as ErrorCode,
    message: error instanceof Error ? error.message : 'An unexpected error occurred',
  };
}
