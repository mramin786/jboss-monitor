// src/api/auth.js
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Helper function to handle API errors
const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'API request failed');
  }
  return await response.json();
};

// Login
export const login = async (username, password) => {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });
  
  return handleResponse(response);
};

// Register
export const register = async (username, password, role = 'user') => {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password, role })
  });
  
  return handleResponse(response);
};

// Get user profile
export const getProfile = async (token) => {
  const response = await fetch(`${API_URL}/auth/profile`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return handleResponse(response);
};

// Store JBoss credentials
export const storeJbossCredentials = async (token, environment, username, password) => {
  const response = await fetch(`${API_URL}/auth/jboss-credentials`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ environment, username, password })
  });
  
  return handleResponse(response);
};

// src/api/hosts.js
export const getHosts = async (token, environment) => {
  const response = await fetch(`${API_URL}/hosts/${environment}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return handleResponse(response);
};

export const addHost = async (token, environment, hostData) => {
  const response = await fetch(`${API_URL}/hosts/${environment}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(hostData)
  });
  
  return handleResponse(response);
};

export const addHostsBulk = async (token, environment, hostsData) => {
  const response = await fetch(`${API_URL}/hosts/${environment}/bulk`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(hostsData)
  });
  
  return handleResponse(response);
};

export const parseBulkInput = async (token, environment, input) => {
  const response = await fetch(`${API_URL}/hosts/${environment}/parse-bulk`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ input })
  });
  
  return handleResponse(response);
};

export const deleteHost = async (token, environment, hostId) => {
  const response = await fetch(`${API_URL}/hosts/${environment}/${hostId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return handleResponse(response);
};

// src/api/monitor.js
export const getMonitorStatus = async (token, environment) => {
  const response = await fetch(`${API_URL}/monitor/${environment}/status`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return handleResponse(response);
};

export const checkHost = async (token, environment, hostId) => {
  const response = await fetch(`${API_URL}/monitor/${environment}/check/${hostId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return handleResponse(response);
};

export const checkAllHosts = async (token, environment) => {
  const response = await fetch(`${API_URL}/monitor/${environment}/check-all`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return handleResponse(response);
};

// src/api/reports.js
export const getReports = async (token) => {
  const response = await fetch(`${API_URL}/reports/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return handleResponse(response);
};

export const generateReport = async (token, environment, username, password, format = 'pdf') => {
  const response = await fetch(`${API_URL}/reports/${environment}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ username, password, format })
  });
  
  return handleResponse(response);
};

export const getReport = async (token, reportId) => {
  const response = await fetch(`${API_URL}/reports/${reportId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return handleResponse(response);
};

export const deleteReport = async (token, reportId) => {
  const response = await fetch(`${API_URL}/reports/${reportId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return handleResponse(response);
};

export const getReportDownloadUrl = (reportId) => {
  return `${API_URL}/reports/${reportId}/download`;
};
