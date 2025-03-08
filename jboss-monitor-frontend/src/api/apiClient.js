// src/api/apiClient.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
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
  
  // Add cache control headers to GET requests
  if (config.method === 'get') {
    config.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
    config.headers['Pragma'] = 'no-cache';
    config.headers['Expires'] = '0';
    
    // Add timestamp to URL to prevent caching
    const timestamp = new Date().getTime();
    const separator = config.url.includes('?') ? '&' : '?';
    config.url = `${config.url}${separator}t=${timestamp}`;
  }
  
  return config;
}, (error) => {
  return Promise.reject(error);
});

export default apiClient;
