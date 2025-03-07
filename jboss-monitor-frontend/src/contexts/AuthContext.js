// src/contexts/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
import { login, register, getProfile } from '../api/auth';

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
          const profile = await getProfile(token);
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
  const handleLogin = async (username, password) => {
    setLoading(true);
    setError(null);

    try {
      const response = await login(username, password);
      
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
  const handleRegister = async (username, password, role = 'user') => {
    setLoading(true);
    setError(null);

    try {
      await register(username, password, role);
      
      // Automatically login after registration
      return await handleLogin(username, password);
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
    // Implementation in the API service
  };

  // Context value
  const value = {
    currentUser,
    token,
    loading,
    error,
    isAuthenticated: !!currentUser,
    login: handleLogin,
    register: handleRegister,
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
  return useContext(AuthContext);
};

export default AuthContext;
