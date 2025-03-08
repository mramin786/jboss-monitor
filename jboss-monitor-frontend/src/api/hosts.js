// src/api/hosts.js
import apiClient from './apiClient';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export const getHosts = async (token, environment) => {
  try {
    const response = await apiClient.get(`/hosts/${environment}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to fetch hosts');
  }
};

export const addHost = async (token, environment, hostData) => {
  try {
    const response = await apiClient.post(`/hosts/${environment}`, hostData);
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to add host');
  }
};

export const addHostsBulk = async (token, environment, hostsData) => {
  try {
    const response = await apiClient.post(`/hosts/${environment}/bulk`, hostsData);
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to add hosts in bulk');
  }
};

export const deleteHost = async (token, environment, hostId) => {
  try {
    const response = await apiClient.delete(`/hosts/${environment}/${hostId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to delete host');
  }
};

export const parseBulkInput = async (token, environment, input) => {
  try {
    const response = await apiClient.post(`/hosts/${environment}/parse-bulk`, { input });
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to parse bulk input');
  }
};
