// src/api/monitor.js
import apiClient from './apiClient';

export const getMonitorStatus = async (token, environment) => {
  try {
    const response = await apiClient.get(`/monitor/${environment}/status`);
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to fetch monitor status');
  }
};

export const checkHost = async (token, environment, hostId) => {
  try {
    const response = await apiClient.post(`/monitor/${environment}/check/${hostId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to check host');
  }
};

export const checkAllHosts = async (token, environment) => {
  try {
    const response = await apiClient.post(`/monitor/${environment}/check-all`);
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to check all hosts');
  }
};
