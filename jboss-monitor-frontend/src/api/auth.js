// src/api/auth.js
import apiClient from './apiClient';

export const login = async (username, password) => {
  try {
    const response = await apiClient.post('/auth/login', { username, password });
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Login failed');
  }
};

export const register = async (username, password, role = 'user') => {
  try {
    const response = await apiClient.post('/auth/register', { 
      username, 
      password, 
      role 
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Registration failed');
  }
};

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
