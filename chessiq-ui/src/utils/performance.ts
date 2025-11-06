/**
 * Performance monitoring utilities
 * Tracks Web Vitals and API call performance
 */

// Track API call performance
export const trackApiCall = async <T>(
  fn: () => Promise<T>,
  endpoint: string
): Promise<T> => {
  const start = performance.now();
  try {
    const result = await fn();
    const duration = performance.now() - start;

    // Log slow requests (> 1 second)
    if (duration > 1000) {
      console.warn(`⚠️ Slow API call: ${endpoint} took ${duration.toFixed(2)}ms`);
    }

    // Log all API calls in development
    if (import.meta.env.DEV) {
      console.log(`[API] ${endpoint} - ${duration.toFixed(2)}ms`);
    }

    return result;
  } catch (error) {
    const duration = performance.now() - start;
    console.error(`❌ API error after ${duration.toFixed(2)}ms:`, error);
    throw error;
  }
};

// Measure page load performance
export const measurePageLoad = () => {
  if (typeof window === 'undefined') return;

  window.addEventListener('load', () => {
    const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    
    if (perfData) {
      const metrics = {
        domContentLoaded: `${(perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart).toFixed(2)}ms`,
        loadComplete: `${(perfData.loadEventEnd - perfData.loadEventStart).toFixed(2)}ms`,
        timeToFirstByte: `${(perfData.responseStart - perfData.requestStart).toFixed(2)}ms`,
        domInteractive: `${(perfData.domInteractive - perfData.domContentLoadedEventStart).toFixed(2)}ms`,
        totalLoadTime: `${(perfData.loadEventEnd - perfData.fetchStart).toFixed(2)}ms`,
      };

      if (import.meta.env.DEV) {
        console.log('📊 Page Load Metrics:', metrics);
      }
    }
  });
};

// Measure component render time (for React components)
export const measureComponentRender = (componentName: string) => {
  const start = performance.now();
  
  return () => {
    const duration = performance.now() - start;
    
    if (duration > 100) {
      console.warn(`⚠️ Slow component render: ${componentName} took ${duration.toFixed(2)}ms`);
    }
    
    if (import.meta.env.DEV) {
      console.log(`[Component] ${componentName} - ${duration.toFixed(2)}ms`);
    }
  };
};

// Initialize performance monitoring
if (typeof window !== 'undefined') {
  measurePageLoad();
}

