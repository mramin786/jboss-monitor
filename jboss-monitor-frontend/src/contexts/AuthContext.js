// src/contexts/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
import * as authApi from '../api/auth';

// Create context
const AuthContext = createContext();

// Auth provider component
export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is authenticated on initial load
  useEffect(() => {
    const verifyToken = async () => {
      if (token) {
        try {
          const profile = await authApi.getProfile(token);
          setCurrentUser(profile);
        } catch (err) {
          console.error('Token verification failed:', err);
          // Clear invalid token
          logout();
        }
      }
      setLoading(false);
    };

    verifyToken();
  }, [token]);

  // Login handler
  const login = async (username, password) => {
    setLoading(true);
    setError(null);

    try {
      const response = await authApi.login(username, password);
      
      // Store token in localStorage
      localStorage.setItem('token', response.token);
      setToken(response.token);
      
      // Set user data
      setCurrentUser({
        username: response.username,
        role: response.role
      });
      
      return response;
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Register handler
  const register = async (username, password, role = 'user') => {
    setLoading(true);
    setError(null);

    try {
      await authApi.register(username, password, role);
      
      // Automatically login after registration
      return await login(username, password);
    } catch (err) {
      setError(err.message || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Logout handler
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setCurrentUser(null);
  };

  // Store JBoss credentials
  const storeJbossCredentials = async (environment, username, password) => {
    try {
      return await authApi.storeJbossCredentials(token, environment, username, password);
    } catch (err) {
      throw err;
    }
  };

  // Context value
  const value = {
    currentUser,
    token,
    loading,
    error,
    isAuthenticated: !!currentUser,
    login,
    register,
    logout,
    storeJbossCredentials
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
