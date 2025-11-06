# Performance Monitoring Guide

This guide explains how to check performance metrics for both frontend and backend of DeepChessIQ.

---

## 🎨 Frontend Performance Monitoring

### 1. Browser DevTools (Built-in)

#### Chrome DevTools Performance Tab
1. **Open DevTools**: Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
2. **Performance Tab**: Click "Performance" tab
3. **Record**: Click record button (circle icon) → Interact with your app → Stop recording
4. **Metrics to Check**:
   - **FPS** (Frames Per Second) - Should be 60fps
   - **CPU Usage** - Check which functions consume most CPU
   - **Memory Usage** - Look for memory leaks
   - **Network Requests** - Check request timing
   - **Rendering Time** - Paint and layout times

#### Lighthouse (Chrome DevTools)
1. **Open DevTools** → **Lighthouse** tab
2. **Select Categories**: Performance, Accessibility, Best Practices, SEO
3. **Click "Analyze page load"**
4. **Key Metrics**:
   - **LCP** (Largest Contentful Paint) - < 2.5s
   - **FID** (First Input Delay) - < 100ms
   - **CLS** (Cumulative Layout Shift) - < 0.1
   - **FCP** (First Contentful Paint) - < 1.8s
   - **TTI** (Time to Interactive) - < 3.8s
   - **Speed Index** - < 3.4s

#### Network Tab
1. **Open DevTools** → **Network** tab
2. **Reload Page** (Cmd+R / Ctrl+R)
3. **Check**:
   - Request count and total size
   - Load time for each resource
   - Waterfall chart showing request sequence
   - Slow requests (red/yellow indicators)

#### React DevTools Profiler
1. **Install React DevTools Extension** (Chrome/Firefox)
2. **Open DevTools** → **Profiler** tab
3. **Click Record** → Interact with app → Stop
4. **Check**:
   - Component render times
   - Re-render frequency
   - Components causing performance issues

### 2. Web Vitals (Code-based Monitoring)

#### Install Web Vitals Library
```bash
cd chessiq-ui
npm install web-vitals
```

#### Add Performance Monitoring
Create `chessiq-ui/src/utils/performance.ts`:
```typescript
import { onCLS, onFID, onFCP, onLCP, onTTFB, onINP } from 'web-vitals';

function sendToAnalytics(metric: any) {
  // Log to console in development
  if (import.meta.env.DEV) {
    console.log('Performance Metric:', {
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      delta: metric.delta,
      id: metric.id,
    });
  }
  
  // In production, send to your analytics service
  // Example: Google Analytics, Sentry, etc.
  // gtag('event', metric.name, { value: metric.value });
}

// Measure Core Web Vitals
onCLS(sendToAnalytics);      // Cumulative Layout Shift
onFID(sendToAnalytics);      // First Input Delay
onFCP(sendToAnalytics);      // First Contentful Paint
onLCP(sendToAnalytics);      // Largest Contentful Paint
onTTFB(sendToAnalytics);     // Time to First Byte
onINP(sendToAnalytics);      // Interaction to Next Paint
```

#### Import in main.tsx
```typescript
// Add at top of chessiq-ui/src/main.tsx
import './utils/performance';
```

### 3. Bundle Size Analysis

#### Vite Bundle Analyzer
```bash
cd chessiq-ui
npm install --save-dev rollup-plugin-visualizer
```

Update `vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      open: true,
      filename: 'dist/stats.html',
      gzipSize: true,
      brotliSize: true,
    })
  ],
})
```

Run build:
```bash
npm run build
# Opens visualization of bundle sizes
```

### 4. API Request Monitoring

Add to `chessiq-ui/src/services/api.ts`:
```typescript
// Add timing wrapper
const apiCallWithTiming = async (fn: () => Promise<any>, endpoint: string) => {
  const start = performance.now();
  try {
    const result = await fn();
    const duration = performance.now() - start;
    
    // Log slow requests (> 1 second)
    if (duration > 1000) {
      console.warn(`Slow API call: ${endpoint} took ${duration.toFixed(2)}ms`);
    }
    
    // Log to analytics in production
    if (import.meta.env.PROD) {
      // Send to your analytics service
    }
    
    return result;
  } catch (error) {
    const duration = performance.now() - start;
    console.error(`API error after ${duration.toFixed(2)}ms:`, error);
    throw error;
  }
};

// Wrap your API calls
export const profileApi = {
  get: () => apiCallWithTiming(() => api.get('/api/profile'), 'GET /api/profile'),
  // ... other methods
};
```

---

## ⚙️ Backend Performance Monitoring

### 1. Response Time Middleware

Create `backend/src/middleware/performance.js`:
```javascript
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
    if (process.env.NODE_ENV === 'development') {
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
```

Add to `backend/src/index.js`:
```javascript
const performanceMiddleware = require('./middleware/performance');

// Add after CORS, before routes
app.use(performanceMiddleware);
```

### 2. Database Query Performance

Create `backend/src/middleware/dbPerformance.js`:
```javascript
/**
 * Database query performance monitoring
 * Wraps database calls to track query times
 */
const { run } = require('../db');

const originalRun = run;
let queryCount = 0;
let totalQueryTime = 0;
const slowQueries = [];

// Wrap the run function
const runWithTiming = async (query, params) => {
  const start = process.hrtime();
  queryCount++;
  
  try {
    const result = await originalRun(query, params);
    const duration = process.hrtime(start);
    const durationMs = duration[0] * 1000 + duration[1] / 1e6;
    
    totalQueryTime += durationMs;
    
    // Log slow queries (> 500ms)
    if (durationMs > 500) {
      slowQueries.push({
        query: query.substring(0, 100), // First 100 chars
        duration: `${durationMs.toFixed(2)}ms`,
        timestamp: new Date().toISOString(),
      });
      console.warn(`⚠️  Slow query (${durationMs.toFixed(2)}ms):`, query.substring(0, 100));
    }
    
    return result;
  } catch (error) {
    const duration = process.hrtime(start);
    const durationMs = duration[0] * 1000 + duration[1] / 1e6;
    console.error(`❌ Query error after ${durationMs.toFixed(2)}ms:`, error.message);
    throw error;
  }
};

// Replace run function
module.exports = {
  run: runWithTiming,
  getStats: () => ({
    totalQueries: queryCount,
    averageQueryTime: queryCount > 0 ? (totalQueryTime / queryCount).toFixed(2) : 0,
    slowQueries: slowQueries.slice(-10), // Last 10 slow queries
  }),
  resetStats: () => {
    queryCount = 0;
    totalQueryTime = 0;
    slowQueries.length = 0;
  },
};
```

### 3. Memory and CPU Monitoring

Create `backend/src/middleware/systemMetrics.js`:
```javascript
/**
 * System resource monitoring
 * Tracks memory and CPU usage
 */
const os = require('os');

function getSystemMetrics() {
  const memUsage = process.memoryUsage();
  const totalMem = os.totalmem();
  const freeMem = os.freemem();
  const usedMem = totalMem - freeMem;

  return {
    process: {
      heapUsed: `${(memUsage.heapUsed / 1024 / 1024).toFixed(2)} MB`,
      heapTotal: `${(memUsage.heapTotal / 1024 / 1024).toFixed(2)} MB`,
      external: `${(memUsage.external / 1024 / 1024).toFixed(2)} MB`,
      rss: `${(memUsage.rss / 1024 / 1024).toFixed(2)} MB`,
    },
    system: {
      totalMemory: `${(totalMem / 1024 / 1024 / 1024).toFixed(2)} GB`,
      freeMemory: `${(freeMem / 1024 / 1024 / 1024).toFixed(2)} GB`,
      usedMemory: `${(usedMem / 1024 / 1024 / 1024).toFixed(2)} GB`,
      memoryUsagePercent: `${((usedMem / totalMem) * 100).toFixed(2)}%`,
      cpuCount: os.cpus().length,
      uptime: `${(os.uptime() / 3600).toFixed(2)} hours`,
    },
    processUptime: `${(process.uptime() / 3600).toFixed(2)} hours`,
  };
}

// Log metrics every 5 minutes
setInterval(() => {
  const metrics = getSystemMetrics();
  console.log('📊 System Metrics:', JSON.stringify(metrics, null, 2));
  
  // Warn if memory usage is high (> 80%)
  const memPercent = parseFloat(metrics.system.memoryUsagePercent);
  if (memPercent > 80) {
    console.warn(`⚠️  High memory usage: ${memPercent}%`);
  }
}, 5 * 60 * 1000); // 5 minutes

// Export for API endpoint
module.exports = {
  getSystemMetrics,
  getMetrics: getSystemMetrics,
};
```

Add metrics endpoint to `backend/src/index.js`:
```javascript
const { getMetrics } = require('./middleware/systemMetrics');

// Add metrics endpoint (protect with auth in production)
app.get('/api/metrics', (req, res) => {
  res.json(getMetrics());
});
```

### 4. API Endpoint Performance Dashboard

Create `backend/src/routes/metrics.js`:
```javascript
const express = require('express');
const router = express.Router();
const { getMetrics } = require('../middleware/systemMetrics');
const { getStats: getDbStats } = require('../middleware/dbPerformance');

// Store endpoint statistics
const endpointStats = {};

// Middleware to track endpoint performance
const trackEndpoint = (req, res, next) => {
  const start = Date.now();
  const endpoint = `${req.method} ${req.path}`;

  res.on('finish', () => {
    const duration = Date.now() - start;
    
    if (!endpointStats[endpoint]) {
      endpointStats[endpoint] = {
        count: 0,
        totalTime: 0,
        minTime: Infinity,
        maxTime: 0,
        errors: 0,
      };
    }

    const stats = endpointStats[endpoint];
    stats.count++;
    stats.totalTime += duration;
    stats.minTime = Math.min(stats.minTime, duration);
    stats.maxTime = Math.max(stats.maxTime, duration);
    
    if (res.statusCode >= 400) {
      stats.errors++;
    }
  });

  next();
};

// Get performance statistics
router.get('/performance', (req, res) => {
  const stats = Object.entries(endpointStats).map(([endpoint, data]) => ({
    endpoint,
    count: data.count,
    averageTime: `${(data.totalTime / data.count).toFixed(2)}ms`,
    minTime: `${data.minTime}ms`,
    maxTime: `${data.maxTime}ms`,
    errorRate: `${((data.errors / data.count) * 100).toFixed(2)}%`,
    totalTime: `${data.totalTime}ms`,
  }));

  res.json({
    endpoints: stats,
    database: getDbStats(),
    system: getMetrics(),
  });
});

module.exports = { router, trackEndpoint };
```

Add to `backend/src/index.js`:
```javascript
const { router: metricsRouter, trackEndpoint } = require('./routes/metrics');

// Track all API routes
app.use('/api', trackEndpoint);

// Metrics endpoint
app.use('/api/metrics', metricsRouter);
```

### 5. Load Testing

#### Using Apache Bench (ab)
```bash
# Install Apache Bench (usually pre-installed on Mac/Linux)
# Test a single endpoint
ab -n 100 -c 10 http://localhost:3000/api/profile

# With authentication
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3000/api/games
```

#### Using Artillery (Node.js)
```bash
cd backend
npm install --save-dev artillery
```

Create `backend/artillery-config.yml`:
```yaml
config:
  target: 'http://localhost:3000'
  phases:
    - duration: 60
      arrivalRate: 10
  defaults:
    headers:
      Authorization: 'Bearer YOUR_TOKEN'
scenarios:
  - name: 'Load Test'
    flow:
      - get:
          url: '/api/profile'
      - get:
          url: '/api/statistics'
      - get:
          url: '/api/games'
```

Run:
```bash
artillery run artillery-config.yml
```

---

## 📊 Quick Performance Checks

### Frontend Quick Check
1. **Open DevTools** → **Lighthouse** → Run audit
2. **Check Network tab** → Look for slow requests
3. **Check Console** → Look for performance warnings
4. **Check Bundle size**: `npm run build` → Check `dist/` folder size

### Backend Quick Check
1. **Start server**: `npm run dev`
2. **Check console** → Look for slow request warnings
3. **Visit**: `http://localhost:3000/api/metrics/performance`
4. **Monitor logs** → Watch for slow queries and errors

---

## 🎯 Performance Targets

### Frontend
- **LCP**: < 2.5 seconds
- **FID**: < 100 milliseconds
- **CLS**: < 0.1
- **Bundle Size**: < 500 KB (gzipped)
- **API Response**: < 500ms

### Backend
- **API Response Time**: < 500ms (p95)
- **Database Queries**: < 100ms (p95)
- **Memory Usage**: < 80% of available
- **Error Rate**: < 1%
- **Uptime**: > 99.9%

---

## 🔧 Production Monitoring Tools

### Recommended Services
1. **Sentry** - Error tracking and performance monitoring
2. **New Relic** - Full-stack APM
3. **Datadog** - Infrastructure and application monitoring
4. **Google Analytics** - Web vitals tracking
5. **Prometheus + Grafana** - Self-hosted metrics

---

## 📝 Next Steps

1. **Implement basic monitoring** using the code examples above
2. **Set up alerts** for slow requests (> 1s) and errors
3. **Create a dashboard** to visualize metrics
4. **Set up continuous monitoring** in production
5. **Regular performance audits** (weekly/monthly)

---

**Last Updated:** October 27, 2025

