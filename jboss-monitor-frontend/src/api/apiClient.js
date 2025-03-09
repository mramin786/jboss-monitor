// src/api/apiClient.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Create an in-memory cache for ETags
const etagCache = new Map();

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  // Add this to handle redirects automatically
  maxRedirects: 5
});

// Add a request interceptor to include auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  // Skip cache-busting for authentication endpoints
  if (config.url && config.url.includes('/auth/')) {
    return config;
  }
  
  // Add cache control headers to all requests
  config.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
  config.headers['Pragma'] = 'no-cache';
  config.headers['Expires'] = '0';
  
  // Add ETag support - send If-None-Match if we have it in cache
  const url = config.url;
  if (url && etagCache.has(url)) {
    config.headers['If-None-Match'] = etagCache.get(url);
  }
  
  // Add timestamp to URL to prevent caching for GET requests
  if (config.method === 'get') {
    const timestamp = new Date().getTime();
    const separator = config.url.includes('?') ? '&' : '?';
    config.url = `${config.url}${separator}t=${timestamp}`;
  }
  
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Add a response interceptor to store ETags
apiClient.interceptors.response.use(
  response => {
    const etag = response.headers['etag'];
    const url = response.config.url;
    
    if (etag && url) {
      // Store ETags without the query parameters
      const baseUrl = url.split('?')[0];
      etagCache.set(baseUrl, etag);
    }
    
    return response;
  },
  error => {
    // Handle 304 Not Modified as a successful response
    if (error.response && error.response.status === 304) {
      // Use cached data
      const originalUrl = error.config.url.split('?')[0];
      // Resolve with empty data since we're using cached data on client side
      return Promise.resolve({
        status: 304,
        statusText: 'Not Modified',
        headers: error.response.headers,
        config: error.config,
        data: {} // We'll use the cached data instead
      });
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
