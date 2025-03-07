// src/pages/DashboardPage.js
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Typography,
  Paper,
  CircularProgress,
  Card,
  CardContent,
  Button,
  Alert,
  Divider
} from '@mui/material';
import {
  Storage as StorageIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HelpOutline as HelpOutlineIcon,
  Speed as SpeedIcon,
  Public as PublicIcon,
  Description as DescriptionIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getMonitorStatus } from '../api/monitor';
import { getReports } from '../api/reports';

// Components for the dashboard
const EnvironmentStatusCard = ({ environment, hosts, loading, error }) => {
  const navigate = useNavigate();
  
  // Compute statistics
  const computeStats = () => {
    if (!hosts || hosts.length === 0) {
      return {
        total: 0,
        up: 0,
        down: 0,
        unknown: 0,
        upPercentage: 0
      };
    }
    
    const total = hosts.length;
    const up = hosts.filter(h => h.status?.instance_status === 'up').length;
    const down = hosts.filter(h => h.status?.instance_status === 'down').length;
    const unknown = total - up - down;
    const upPercentage = (up / total) * 100;
    
    return { total, up, down, unknown, upPercentage };
  };
  
  const stats = computeStats();
  const envTitle = environment === 'production' ? 'Production' : 'Non-Production';
  const envColor = environment === 'production' ? 'error.main' : 'info.main';
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <StorageIcon sx={{ fontSize: 28, color: envColor, mr: 1 }} />
          <Typography variant="h6" component="div">
            {envTitle} Environment
          </Typography>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : (
          <>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 2, 
                    textAlign: 'center',
                    backgroundColor: 'background.paper'
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    Total Hosts
                  </Typography>
                  <Typography variant="h4">
                    {stats.total}
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={6}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 2, 
                    textAlign: 'center',
                    backgroundColor: 'success.dark',
                    color: 'white'
                  }}
                >
                  <Typography variant="body2">
                    Uptime
                  </Typography>
                  <Typography variant="h4">
                    {stats.upPercentage.toFixed(1)}%
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={4}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center'
                  }}
                >
                  <CheckCircleIcon color="success" />
                  <Typography variant="h6">{stats.up}</Typography>
                  <Typography variant="body2" color="text.secondary">UP</Typography>
                </Box>
              </Grid>
              
              <Grid item xs={4}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center'
                  }}
                >
                  <ErrorIcon color="error" />
                  <Typography variant="h6">{stats.down}</Typography>
                  <Typography variant="body2" color="text.secondary">DOWN</Typography>
                </Box>
              </Grid>
              
              <Grid item xs={4}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center'
                  }}
                >
                  <HelpOutlineIcon color="disabled" />
                  <Typography variant="h6">{stats.unknown}</Typography>
                  <Typography variant="body2" color="text.secondary">UNKNOWN</Typography>
                </Box>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
              <Button 
                variant="outlined" 
                size="small"
                onClick={() => navigate(`/${environment}/hosts`)}
              >
                Manage Hosts
              </Button>
              
              <Button 
                variant="contained" 
                size="small"
                onClick={() => navigate(`/${environment}/monitor`)}
              >
                View Monitor
              </Button>
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

const RecentReportsCard = ({ reports, loading, error }) => {
  const navigate = useNavigate();
  
  const getRecentReports = () => {
    if (!reports || reports.length === 0) {
      return [];
    }
    
    // Sort by creation date (newest first) and limit to 5
    return [...reports]
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 5);
  };
  
  const recentReports = getRecentReports();
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <DescriptionIcon sx={{ fontSize: 28, color: 'warning.main', mr: 1 }} />
          <Typography variant="h6" component="div">
            Recent Reports
          </Typography>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : recentReports.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <Typography variant="body2" color="text.secondary">
              No reports generated yet
            </Typography>
          </Box>
        ) : (
          <>
            {recentReports.map((report) => (
              <Paper 
                key={report.id}
                elevation={0}
                sx={{ 
                  p: 1.5, 
                  mb: 1, 
                  backgroundColor: 'background.paper',
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'action.hover'
                  }
                }}
                onClick={() => navigate(`/reports/${report.id}`)}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                    {report.environment === 'production' ? 'Production' : 'Non-Production'} Report
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {report.format.toUpperCase()}
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {new Date(report.created_at).toLocaleString()}
                </Typography>
              </Paper>
            ))}
            
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button 
                variant="outlined" 
                size="small"
                onClick={() => navigate('/reports')}
              >
                View All Reports
              </Button>
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

const SystemOverviewCard = () => {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <SpeedIcon sx={{ fontSize: 28, color: 'primary.main', mr: 1 }} />
          <Typography variant="h6" component="div">
            System Overview
          </Typography>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <PublicIcon sx={{ fontSize: 80, color: 'primary.main', opacity: 0.7 }} />
          <Typography variant="h5" sx={{ mt: 2 }}>
            JBoss Monitor
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Monitor your JBoss servers in real-time
          </Typography>
        </Box>
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2">
            Welcome to the JBoss Monitoring System. This dashboard provides an overview of your 
            JBoss instances across Production and Non-Production environments.
          </Typography>
          <Typography variant="body2" sx={{ mt: 1.5 }}>
            Use the sidebar navigation to manage hosts, monitor instances, and generate reports.
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

// Main Dashboard Page
const DashboardPage = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState({
    production: true,
    non_production: true,
    reports: true
  });
  const [error, setError] = useState({
    production: null,
    non_production: null,
    reports: null
  });
  const [data, setData] = useState({
    production: [],
    non_production: [],
    reports: []
  });

  // Load data on mount
  useEffect(() => {
    const fetchData = async () => {
      // Fetch production status
      try {
        const productionData = await getMonitorStatus(token, 'production');
        setData(prev => ({ ...prev, production: productionData }));
      } catch (err) {
        setError(prev => ({ ...prev, production: err.message || 'Failed to load production data' }));
      } finally {
        setLoading(prev => ({ ...prev, production: false }));
      }
      
      // Fetch non-production status
      try {
        const nonProdData = await getMonitorStatus(token, 'non_production');
        setData(prev => ({ ...prev, non_production: nonProdData }));
      } catch (err) {
        setError(prev => ({ ...prev, non_production: err.message || 'Failed to load non-production data' }));
      } finally {
        setLoading(prev => ({ ...prev, non_production: false }));
      }
      
      // Fetch reports
      try {
        const reportsData = await getReports(token);
        setData(prev => ({ ...prev, reports: reportsData }));
      } catch (err) {
        setError(prev => ({ ...prev, reports: err.message || 'Failed to load reports' }));
      } finally {
        setLoading(prev => ({ ...prev, reports: false }));
      }
    };

    fetchData();
    
    // Set up refresh interval (every 30 seconds)
    const intervalId = setInterval(() => {
      fetchData();
    }, 30000);
    
    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, [token]);

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <SystemOverviewCard />
        </Grid>
        
        <Grid item xs={12} md={4}>
          <EnvironmentStatusCard 
            environment="production"
            hosts={data.production}
            loading={loading.production}
            error={error.production}
          />
        </Grid>
        
        <Grid item xs={12} md={4}>
          <EnvironmentStatusCard 
            environment="non_production"
            hosts={data.non_production}
            loading={loading.non_production}
            error={error.non_production}
          />
        </Grid>
        
        <Grid item xs={12}>
          <RecentReportsCard 
            reports={data.reports}
            loading={loading.reports}
            error={error.reports}
          />
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;
