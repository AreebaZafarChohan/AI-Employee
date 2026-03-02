/**
 * Jest Test Setup
 * Configures test environment for all test files
 */

// Mock console.error in tests to reduce noise (can be overridden per test)
beforeAll(() => {
  // Suppress console.error during tests unless explicitly needed
  jest.spyOn(console, 'error').mockImplementation(() => {});
});

// Clean up after all tests
afterAll(() => {
  // Restore all mocks
  jest.restoreAllMocks();
});

// Global test timeout
jest.setTimeout(10000);
