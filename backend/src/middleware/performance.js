/**
 * Performance monitoring middleware
 * Logs request duration and slow endpoints
 */
const performanceMiddleware = (req, res, next) => {
  const start = Date.now();
  const startHrTime = process.hrtime();

  // Log when response finishes
  res.on('finish', () => {
    const duration = Date.now() - start;
    const hrDuration = process.hrtime(startHrTime);
    const durationMs = hrDuration[0] * 1000 + hrDuration[1] / 1e6;

    const logData = {
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      durationMs: duration.toFixed(2),
      timestamp: new Date().toISOString(),
    };

    // Log all requests in development
    if (process.env.NODE_ENV === 'development' || process.env.NODE_ENV !== 'production') {
      console.log(`[${logData.method}] ${logData.path} - ${logData.statusCode} - ${logData.duration}`);
    }

    // Warn about slow requests (> 1 second)
    if (duration > 1000) {
      console.warn(`⚠️  Slow request detected:`, logData);
    }

    // Log errors (> 500ms or 4xx/5xx status)
    if (duration > 500 || res.statusCode >= 400) {
      console.error(`❌ Performance issue:`, logData);
    }
  });

  next();
};

module.exports = performanceMiddleware;

