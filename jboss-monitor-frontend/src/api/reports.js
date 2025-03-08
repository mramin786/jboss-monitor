// src/api/reports.js
import apiClient from './apiClient';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export const getReports = async (token) => {
  try {
    const response = await apiClient.get('/reports');
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to fetch reports');
  }
};

export const generateReport = async (token, environment, username, password, format = 'pdf') => {
  try {
    const response = await apiClient.post(`/reports/${environment}/generate`, { 
      username, 
      password, 
      format 
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to generate report');
  }
};

export const deleteReport = async (token, reportId) => {
  try {
    const response = await apiClient.delete(`/reports/${reportId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to delete report');
  }
};

export const getReportDownloadUrl = (reportId) => {
  return `${API_URL}/reports/${reportId}/download`;
};
