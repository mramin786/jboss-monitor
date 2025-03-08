// src/api/reports.js
import apiClient from './apiClient';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export const getReports = async () => {
  try {
    const response = await apiClient.get('/reports/');
    return response.data;
  } catch (error) {
    console.error("Error fetching reports:", error);
    throw error.response?.data || new Error('Failed to fetch reports');
  }
};

export const generateReport = async (token, environment, username, password, format = 'pdf') => {
  try {
    // This should be /api/reports/{environment}/generate without the trailing slash
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
    // This should be /api/reports/{reportId} without the trailing slash
    const response = await apiClient.delete(`/reports/${reportId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || new Error('Failed to delete report');
  }
};
export const getReportDownloadUrl = (reportId) => {
  // Add cache buster to download URL
  const timestamp = new Date().getTime();
  return `${API_URL}/reports/${reportId}/download?t=${timestamp}`;
};

// New function for direct download using proper Authorization header
export const downloadReport = async (reportId) => {
  try {
    const response = await apiClient.get(`/reports/${reportId}/download`, {
      responseType: 'blob' // Important for handling file downloads
    });
    
    // Create a blob URL and trigger download
    const blob = new Blob([response.data], { 
      type: response.headers['content-type'] 
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Get filename from Content-Disposition header if available
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'report';
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1];
      }
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return true;
  } catch (error) {
    console.error("Error downloading report:", error);
    throw error.response?.data || new Error('Failed to download report');
  }
};
