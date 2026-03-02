/**
 * Zod Validation Middleware
 * Validates request bodies using Zod schemas
 */

import { Request, Response, NextFunction } from 'express';
import { ZodSchema, ZodError } from 'zod';
import { ValidationError } from '../utils/errors';

/**
 * Creates validation middleware for a given Zod schema
 * @param schema - Zod schema to validate against
 * @param location - Where to validate (body, query, params)
 */
export function validateRequest<T extends ZodSchema>(
  schema: T,
  location: 'body' | 'query' | 'params' = 'body'
) {
  return (req: Request, _res: Response, next: NextFunction): void => {
    try {
      const validatedData = schema.parse(req[location]);

      // Replace the request data with validated data (includes type transformations)
      req[location] = validatedData;

      next();
    } catch (error) {
      if (error instanceof ZodError) {
        const details = error.errors.map((err) => ({
          field: err.path.join('.'),
          message: err.message,
          code: err.code,
        }));

        const validationError = new ValidationError(
          `Validation failed for ${location}`,
          'VALIDATION_ERROR'
        );
        (validationError as ValidationError & { details: unknown[] }).details = details;

        next(validationError);
      } else {
        next(error);
      }
    }
  };
}

export default validateRequest;
