// src/api/auth.js
import axios from 'axios';
import apiClient from './apiClient';

// API URL for auth requests
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// For login and registration, use direct axios without cache-busting
export const login = async (username, password) => {
  try {
    // Use direct axios call without cache-busting for auth
    const response = await axios.post(`${API_URL}/auth/login`, { 
      username, 
      password 
    });
    return response.data;
  } catch (error) {
    console.error("Login error:", error);
    throw error.response?.data || new Error('Login failed');
  }
};

export const register = async (username, password, role = 'user') => {
  try {
    // Use direct axios call without cache-busting for auth
    const response = await axios.post(`${API_URL}/auth/register`, { 
      username, 
      password, 
      role 
    });
    return response.data;
  } catch (error) {
    console.error("Registration error:", error);
    throw error.response?.data || new Error('Registration failed');
  }
};

// For other auth operations, use the regular apiClient
export const getProfile = async (token) => {
  try {
    const response = await apiClient.get('/auth/profile');
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to fetch profile');
  }
};

export const storeJbossCredentials = async (token, environment, username, password) => {
  try {
    const response = await apiClient.post('/auth/jboss-credentials', { 
      environment, 
      username, 
      password 
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to store JBoss credentials');
  }
};
