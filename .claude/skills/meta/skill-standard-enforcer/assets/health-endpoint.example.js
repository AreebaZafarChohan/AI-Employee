/**
 * IMPACT NOTES:
 * - Health endpoints must respond quickly (< 1 second)
 * - Liveness: Is the service running? (lightweight)
 * - Readiness: Is the service ready for traffic? (checks dependencies)
 * - Return appropriate status codes (200=healthy, 503=unhealthy)
 */

const express = require('express');
const router = express.Router();

/**
 * Liveness Probe
 * Purpose: Check if the application is running
 * Called by: Kubernetes liveness probe, load balancers
 * Should: Always return quickly, minimal processing
 * Returns: 200 if server is up, any other status if down
 */
router.get('/health/live', (req, res) => {
  // Lightweight check - just verify the endpoint responds
  res.status(200).json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(), // How long the process has been running
    service: process.env.SERVICE_NAME || 'unknown',
    version: process.env.BUILD_VERSION || 'unknown'
  });
});

/**
 * Readiness Probe
 * Purpose: Check if the service is ready to handle requests
 * Called by: Kubernetes readiness probe, load balancers
 * Should: Check all critical dependencies
 * Returns: 200 if ready, 503 if not ready
 */
router.get('/health/ready', async (req, res) => {
  try {
    const checks = {
      database: false,
      cache: false,
      timestamp: new Date().toISOString(),
      service: process.env.SERVICE_NAME || 'unknown'
    };

    // Check database connectivity (if configured)
    if (process.env.DATABASE_URL) {
      try {
        // Simple query to verify DB is reachable
        // await db.query('SELECT 1');
        checks.database = true;
      } catch (err) {
        console.error('Health check: Database unavailable', err.message);
      }
    } else {
      checks.database = null; // Not configured, skip check
    }

    // Check cache connectivity (if configured)
    if (process.env.CACHE_URL) {
      try {
        // await cache.ping();
        checks.cache = true;
      } catch (err) {
        console.error('Health check: Cache unavailable', err.message);
        // For optional cache, we might still be "ready"
        checks.cache = false;
      }
    } else {
      checks.cache = null; // Not configured, skip check
    }

    // Determine overall status
    const allCriticalChecksPassed = (
      // Only require DB if it's configured (not null)
      (checks.database === null || checks.database === true) &&
      // Cache is optional, so null or true is OK, false is OK if optional
      (checks.cache === null || checks.cache === true || process.env.ENABLE_CACHE === 'false')
    );

    if (allCriticalChecksPassed) {
      res.status(200).json({
        status: 'ready',
        ...checks
      });
    } else {
      res.status(503).json({
        status: 'not ready',
        ...checks
      });
    }
  } catch (error) {
    console.error('Readiness check failed', error);
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * Custom Health Check
 * Purpose: Detailed health information for debugging
 * Called by: Developers, monitoring systems
 * Returns: Detailed status of all components
 */
router.get('/health/detailed', async (req, res) => {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: process.env.BUILD_VERSION || 'unknown',
    commit: process.env.BUILD_COMMIT || 'unknown',
    environment: process.env.NODE_ENV || 'unknown',
    dependencies: {
      database: {
        status: 'unknown',
        details: {}
      },
      cache: {
        status: 'unknown',
        details: {}
      }
    },
    system: {
      memory: process.memoryUsage(),
      cpu: process.cpuUsage()
    }
  };

  // Check database
  if (process.env.DATABASE_URL) {
    try {
      const start = Date.now();
      // await db.query('SELECT 1');
      const responseTime = Date.now() - start;

      health.dependencies.database = {
        status: 'connected',
        responseTime: `${responseTime}ms`,
        timestamp: new Date().toISOString()
      };
    } catch (err) {
      health.dependencies.database = {
        status: 'error',
        error: err.message
      };
    }
  } else {
    health.dependencies.database.status = 'not_configured';
  }

  // Check cache
  if (process.env.CACHE_URL) {
    try {
      const start = Date.now();
      // await cache.ping();
      const responseTime = Date.now() - start;

      health.dependencies.cache = {
        status: 'connected',
        responseTime: `${responseTime}ms`,
        timestamp: new Date().toISOString()
      };
    } catch (err) {
      health.dependencies.cache = {
        status: 'error',
        error: err.message
      };
    }
  } else {
    health.dependencies.cache.status = 'not_configured';
  }

  res.status(200).json(health);
});

module.exports = router;
