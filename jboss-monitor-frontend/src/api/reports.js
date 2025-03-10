// src/api/reports.js
import apiClient from './apiClient';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export const getReports = async () => {
  try {
    // Add trailing slash to match Flask's route
    const response = await apiClient.get('/reports/');
    return response.data;
  } catch (error) {
    console.error("Error fetching reports:", error);
    throw error.response?.data || new Error('Failed to fetch reports');
  }
};

export const generateReport = async (token, environment, username, password) => {
  try {
    console.log(`Generating PDF report for ${environment}`);
    // Remove trailing slash - this is the key fix
    const response = await apiClient.post(`/reports/${environment}/generate`, { 
      username, 
      password
      // No format parameter - always PDF now
    });
    return response.data;
  } catch (error) {
    console.error("Error generating report:", error);
    throw error.response?.data || new Error('Failed to generate report');
  }
};

export const deleteReport = async (token, reportId) => {
  try {
    console.log(`Deleting report: ${reportId}`);
    // Remove trailing slash - this is the key fix
    const response = await apiClient.delete(`/reports/${reportId}`);
    return response.data;
  } catch (error) {
    console.error("Error deleting report:", error);
    throw error.response?.data || new Error('Failed to delete report');
  }
};

export const getReportDownloadUrl = (reportId) => {
  // Add cache buster to download URL
  const timestamp = new Date().getTime();
  return `${API_URL}/reports/${reportId}/download?t=${timestamp}`;
};

// Enhanced download function with better error handling
export const downloadReport = async (reportId) => {
  try {
    console.log(`Downloading report: ${reportId}`);
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
    let filename = 'report.pdf'; // Default to PDF extension
    
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
export const compareReports = async (token, report1Id, report2Id) => {
  try {
    console.log(`Comparing reports ${report1Id} and ${report2Id}`);
    const response = await apiClient.post('/reports/compare', { 
      report1_id: report1Id, 
      report2_id: report2Id
    });
    return response.data;
  } catch (error) {
    console.error("Error comparing reports:", error);
    throw error.response?.data || new Error('Failed to compare reports');
  }
};

export const getComparisons = async () => {
  try {
    const response = await apiClient.get('/reports/comparisons');
    return response.data;
  } catch (error) {
    console.error("Error fetching comparisons:", error);
    throw error.response?.data || new Error('Failed to fetch comparison reports');
  }
};

export const getComparisonDownloadUrl = (comparisonId) => {
  // Add cache buster to download URL
  const timestamp = new Date().getTime();
  return `${API_URL}/reports/comparison/${comparisonId}/download?t=${timestamp}`;
};

export const downloadComparison = async (comparisonId) => {
  try {
    console.log(`Downloading comparison report: ${comparisonId}`);
    const response = await apiClient.get(`/reports/comparison/${comparisonId}/download`, {
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
    let filename = 'comparison.pdf';
    
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
    console.error("Error downloading comparison report:", error);
    throw error.response?.data || new Error('Failed to download comparison report');
  }
};
// Function to cleanup old reports (admin only)
export const cleanupReports = async (environment = null, maxReports = 10) => {
  try {
    const response = await apiClient.post('/reports/cleanup', {
      environment,
      max_reports: maxReports
    });
    return response.data;
  } catch (error) {
    console.error("Error cleaning up reports:", error);
    throw error.response?.data || new Error('Failed to clean up reports');
  }
};
