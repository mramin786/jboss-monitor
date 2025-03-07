// src/App.js
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';

// Theme
import darkTheme from './themes/darkTheme';

// Context providers
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import HostsPage from './pages/HostsPage';
import HostDetailsPage from './pages/HostDetailsPage';
import MonitorPage from './pages/MonitorPage';
import ReportsPage from './pages/ReportsPage';
import ReportDetailsPage from './pages/ReportDetailsPage';
import NotFoundPage from './pages/NotFoundPage';

// Components
import Header from './components/common/Header';
import Sidebar from './components/common/Sidebar';
import { Box } from '@mui/material';

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  return children;
};

// Main App layout with sidebar and header
const AppLayout = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Sidebar />
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <Header />
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            {/* Protected routes */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <DashboardPage />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/production/hosts" 
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <HostsPage environment="production" />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/non_production/hosts" 
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <HostsPage environment="non_production" />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/:environment/hosts/:hostId" 
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <HostDetailsPage />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/production/monitor" 
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <MonitorPage environment="production" />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/non_production/monitor" 
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <MonitorPage environment="non_production" />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/reports" 
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ReportsPage />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/reports/:reportId" 
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ReportDetailsPage />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
