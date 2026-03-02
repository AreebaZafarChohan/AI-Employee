/**
 * API Types
 * Common types for API responses and errors
 */

/**
 * Standard API error structure
 */
export interface ApiError {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Error codes returned by the API
 */
export type ErrorCode =
  | 'TASK_NOT_FOUND'
  | 'INVALID_INPUT'
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'RATE_LIMITED'
  | 'INTERNAL_ERROR'
  | 'SERVICE_UNAVAILABLE';

/**
 * Success response wrapper
 */
export interface SuccessResponse<T> {
  data: T;
}

/**
 * Paginated response for list endpoints
 */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}
