// src/pages/MonitorPage.js
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Button,
  CircularProgress,
  Alert,
  Snackbar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Help as HelpIcon,
  DataObject as DataObjectIcon,
  PictureAsPdf as PdfIcon,
  TableChart as TableChartIcon,
  Storage as StorageIcon,
  Computer as ComputerIcon,
  DnsRounded as DnsIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import StatusBadge from '../components/common/StatusBadge';
import { getMonitorStatus, checkAllHosts, checkHost } from '../api/monitor';
import { generateReport } from '../api/reports';

// Generate Report Dialog Component
const GenerateReportDialog = ({ open, onClose, onSubmit, environment }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [format, setFormat] = useState('pdf');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      await onSubmit(username, password, format);
      handleReset();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };
  
  const handleReset = () => {
    setUsername('');
    setPassword('');
    setError('');
  };
  
  const handleCancel = () => {
    handleReset();
    onClose();
  };

  const envName = environment === 'production' ? 'Production' : 'Non-Production';

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="sm" fullWidth>
      <DialogTitle>Generate {envName} Status Report</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Enter your JBoss credentials to generate a detailed status report.
            The report will perform a fresh check of all your hosts.
          </Typography>
          
          <TextField
            autoFocus
            margin="dense"
            id="reportUsername"
            label="JBoss Username"
            type="text"
            fullWidth
            variant="outlined"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={loading}
          />
          
          <TextField
            margin="dense"
            id="reportPassword"
            label="JBoss Password"
            type="password"
            fullWidth
            variant="outlined"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
          
          <FormControl fullWidth margin="dense">
            <InputLabel id="format-label">Report Format</InputLabel>
            <Select
              labelId="format-label"
              id="format"
              value={format}
              label="Report Format"
              onChange={(e) => setFormat(e.target.value)}
              disabled={loading}
            >
              <MenuItem value="pdf">PDF Document</MenuItem>
              <MenuItem value="csv">CSV Spreadsheet</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancel} disabled={loading}>
            Cancel
          </Button>
          <Button 
            type="submit" 
            variant="contained" 
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : format === 'pdf' ? <PdfIcon /> : <TableChartIcon />}
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

// Host Status Card Component
const HostStatusCard = ({ host, onRefresh }) => {
  const [expanded, setExpanded] = useState(false);
  
  // Format the last check time
  const formatLastCheck = (lastCheck) => {
    if (!lastCheck) return 'Never';
    
    try {
      return new Date(lastCheck).toLocaleString();
    } catch (e) {
      return lastCheck;
    }
  };
  
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'up': return 'success';
      case 'down': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };
  
  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'up': return <CheckCircleIcon color="success" />;
      case 'down': return <ErrorIcon color="error" />;
      default: return <HelpIcon color="disabled" />;
    }
  };
  
  // Count up and down items
  const getDatasourceCounts = () => {
    const datasources = host.status?.datasources || [];
    const up = datasources.filter(ds => ds.status === 'up').length;
    const down = datasources.filter(ds => ds.status === 'down').length;
    
    return { total: datasources.length, up, down };
  };
  
  const getDeploymentCounts = () => {
    const deployments = host.status?.deployments || [];
    const up = deployments.filter(d => d.status === 'up').length;
    const down = deployments.filter(d => d.status === 'down').length;
    
    return { total: deployments.length, up, down };
  };
  
  const dsCount = getDatasourceCounts();
  const depCount = getDeploymentCounts();
  
  return (
    <Card>
      <CardHeader
        avatar={
          <Avatar 
            sx={{ 
              bgcolor: getStatusColor(host.status?.instance_status) + '.light',
              color: getStatusColor(host.status?.instance_status) + '.dark'
            }}
          >
            <ComputerIcon />
          </Avatar>
        }
        title={`${host.host} (${host.port})`}
        subheader={host.instance}
        action={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <StatusBadge status={host.status?.instance_status || 'unknown'} />
            <Button 
              size="small" 
              startIcon={<RefreshIcon />}
              onClick={() => onRefresh(host)}
            >
              Refresh
            </Button>
          </Box>
        }
      />
      <Divider />
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">
              Last Check:
            </Typography>
            <Typography variant="body2">
              {formatLastCheck(host.status?.last_check)}
            </Typography>
          </Grid>
          
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">
              Status:
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {getStatusIcon(host.status?.instance_status)}
              <Typography variant="body2">
                {(host.status?.instance_status || 'Unknown').toUpperCase()}
              </Typography>
            </Box>
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 2 }} />
        
        <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="details-content"
            id="details-header"
          >
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <StorageIcon color="primary" fontSize="small" />
                  <Typography variant="body2">
                    Datasources: {dsCount.total}
                  </Typography>
                </Box>
                <Box sx={{ mt: 0.5, display: 'flex', gap: 1 }}>
                  <Chip 
                    size="small" 
                    color="success" 
                    label={`${dsCount.up} UP`} 
                    variant="outlined"
                  />
                  {dsCount.down > 0 && (
                    <Chip 
                      size="small" 
                      color="error" 
                      label={`${dsCount.down} DOWN`} 
                      variant="outlined"
                    />
                  )}
                </Box>
              </Grid>
              
              <Grid item xs={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <DnsIcon color="primary" fontSize="small" />
                  <Typography variant="body2">
                    Deployments: {depCount.total}
                  </Typography>
                </Box>
                <Box sx={{ mt: 0.5, display: 'flex', gap: 1 }}>
                  <Chip 
                    size="small" 
                    color="success" 
                    label={`${depCount.up} UP`} 
                    variant="outlined"
                  />
                  {depCount.down > 0 && (
                    <Chip 
                      size="small" 
                      color="error" 
                      label={`${depCount.down} DOWN`} 
                      variant="outlined"
                    />
                  )}
                </Box>
              </Grid>
            </Grid>
          </AccordionSummary>
          <AccordionDetails>
            <Divider sx={{ mb: 2 }} />
            
            {/* Datasources */}
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Datasources
            </Typography>
            
            {host.status?.datasources?.length > 0 ? (
              <List disablePadding dense>
                {host.status.datasources.map((ds, index) => (
                  <ListItem 
                    key={index}
                    sx={{ 
                      py: 0.5,
                      borderRadius: 1,
                      mb: 0.5,
                      bgcolor: ds.status === 'up' ? 'success.dark' : 'error.dark',
                      opacity: 0.8
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      {ds.status === 'up' ? (
                        <CheckCircleIcon color="success" fontSize="small" />
                      ) : (
                        <ErrorIcon color="error" fontSize="small" />
                      )}
                    </ListItemIcon>
                    <ListItemText 
                      primary={ds.name} 
                      secondary={ds.type}
                      primaryTypographyProps={{ variant: 'body2' }}
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                No datasources found
              </Typography>
            )}
            
            <Divider sx={{ my: 2 }} />
            
            {/* Deployments */}
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Deployments (WAR Files)
            </Typography>
            
            {host.status?.deployments?.length > 0 ? (
              <List disablePadding dense>
                {host.status.deployments.map((dep, index) => (
                  <ListItem 
                    key={index}
                    sx={{ 
                      py: 0.5,
                      borderRadius: 1,
                      mb: 0.5,
                      bgcolor: dep.status === 'up' ? 'success.dark' : 'error.dark',
                      opacity: 0.8
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      {dep.status === 'up' ? (
                        <CheckCircleIcon color="success" fontSize="small" />
                      ) : (
                        <ErrorIcon color="error" fontSize="small" />
                      )}
                    </ListItemIcon>
                    <ListItemText 
                      primary={dep.name}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No deployments found
              </Typography>
            )}
          </AccordionDetails>
        </Accordion>
      </CardContent>
    </Card>
  );
};

// Main Monitoring Page
const MonitorPage = ({ environment }) => {
  const [hosts, setHosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });
  
  const { token } = useAuth();
  const navigate = useNavigate();
  
  const envTitle = environment === 'production' ? 'Production' : 'Non-Production';
  
  // Fetch hosts on mount and when environment changes
  useEffect(() => {
    const fetchHosts = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const hostsData = await getMonitorStatus(token, environment);
        setHosts(hostsData);
      } catch (err) {
        setError(err.message || `Failed to load ${envTitle} hosts`);
      } finally {
        setLoading(false);
      }
    };
    
    fetchHosts();
    
    // Set up refresh interval (every 30 seconds)
    const intervalId = setInterval(() => {
      fetchHosts();
    }, 30000);
    
    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, [token, environment, envTitle]);
  
  // Compute dashboard statistics
  const getStats = () => {
    const total = hosts.length;
    const up = hosts.filter(h => h.status?.instance_status === 'up').length;
    const down = hosts.filter(h => h.status?.instance_status === 'down').length;
    const unknown = total - up - down;
    
    const upPercentage = total > 0 ? (up / total) * 100 : 0;
    
    // Count datasources and deployments
    let totalDatasources = 0;
    let upDatasources = 0;
    let totalDeployments = 0;
    let upDeployments = 0;
    
    hosts.forEach(host => {
      const datasources = host.status?.datasources || [];
      totalDatasources += datasources.length;
      upDatasources += datasources.filter(ds => ds.status === 'up').length;
      
      const deployments = host.status?.deployments || [];
      totalDeployments += deployments.length;
      upDeployments += deployments.filter(d => d.status === 'up').length;
    });
    
    return {
      hosts: { total, up, down, unknown, upPercentage },
      datasources: { 
        total: totalDatasources, 
        up: upDatasources,
        upPercentage: totalDatasources > 0 ? (upDatasources / totalDatasources) * 100 : 0
      },
      deployments: { 
        total: totalDeployments, 
        up: upDeployments,
        upPercentage: totalDeployments > 0 ? (upDeployments / totalDeployments) * 100 : 0
      }
    };
  };
  
  const stats = getStats();
  
  // Handle refresh all hosts
  const handleRefreshAll = async () => {
    try {
      await checkAllHosts(token, environment);
      
      setSnackbar({
        open: true,
        message: 'Refreshing all hosts...',
        severity: 'info'
      });
      
      // Refresh the data after a short delay
      setTimeout(() => {
        getMonitorStatus(token, environment)
          .then(data => setHosts(data))
          .catch(err => console.error('Failed to refresh hosts:', err));
      }, 2000);
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message || 'Failed to refresh hosts',
        severity: 'error'
      });
    }
  };
  
  // Handle refresh single host
  const handleRefreshHost = async (host) => {
    try {
      await checkHost(token, environment, host.id);
      
      setSnackbar({
        open: true,
        message: `Refreshing ${host.host}...`,
        severity: 'info'
      });
      
      // Refresh the data after a short delay
      setTimeout(() => {
        getMonitorStatus(token, environment)
          .then(data => setHosts(data))
          .catch(err => console.error('Failed to refresh hosts:', err));
      }, 2000);
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message || 'Failed to refresh host',
        severity: 'error'
      });
    }
  };
  
  // Handle generate report
  const handleGenerateReport = async (username, password, format) => {
    try {
      const result = await generateReport(token, environment, username, password, format);
      
      setSnackbar({
        open: true,
        message: 'Report generation initiated',
        severity: 'success'
      });
      
      // Navigate to the reports page
      navigate('/reports');
      
      return result;
    } catch (err) {
      throw err;
    }
  };
  
  // Close snackbar
  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // Render a spinner while loading
  if (loading && !hosts.length) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', my: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          {envTitle} Monitoring
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefreshAll}
          >
            Refresh All
          </Button>
          
          <Button
            variant="contained"
            startIcon={<PdfIcon />}
            onClick={() => setGenerateDialogOpen(true)}
          >
            Generate Report
          </Button>
        </Box>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <ComputerIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Hosts</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="h4" color="text.primary" align="center">
                  {stats.hosts.total}
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center">
                  Total Hosts
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="h4" color="success.main" align="center">
                  {stats.hosts.upPercentage.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center">
                  Uptime
                </Typography>
              </Grid>
              <Grid item xs={4}>
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <CheckCircleIcon color="success" />
                  <Typography variant="body2">{stats.hosts.up} UP</Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <ErrorIcon color="error" />
                  <Typography variant="body2">{stats.hosts.down} DOWN</Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <HelpIcon color="disabled" />
                  <Typography variant="body2">{stats.hosts.unknown} UNKNOWN</Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <StorageIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Datasources</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="h4" color="text.primary" align="center">
                  {stats.datasources.total}
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center">
                  Total Datasources
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="h4" color="success.main" align="center">
                  {stats.datasources.upPercentage.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center">
                  Availability
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ mt: 1, display: 'flex', justifyContent: 'center', gap: 2 }}>
                  <Chip 
                    icon={<CheckCircleIcon />} 
                    color="success" 
                    label={`${stats.datasources.up} UP`} 
                  />
                  <Chip 
                    icon={<ErrorIcon />} 
                    color="error" 
                    label={`${stats.datasources.total - stats.datasources.up} DOWN`} 
                  />
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <DnsIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Deployments</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="h4" color="text.primary" align="center">
                  {stats.deployments.total}
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center">
                  Total Deployments
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="h4" color="success.main" align="center">
                  {stats.deployments.upPercentage.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center">
                  Availability
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ mt: 1, display: 'flex', justifyContent: 'center', gap: 2 }}>
                  <Chip 
                    icon={<CheckCircleIcon />} 
                    color="success" 
                    label={`${stats.deployments.up} UP`} 
                  />
                  <Chip 
                    icon={<ErrorIcon />} 
                    color="error" 
                    label={`${stats.deployments.total - stats.deployments.up} DOWN`} 
                  />
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
      
      {/* Host Status Cards */}
      {hosts.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary">
            No hosts found
          </Typography>
          <Button 
            variant="outlined" 
            sx={{ mt: 2 }}
            onClick={() => navigate(`/${environment}/hosts`)}
          >
            Add Hosts
          </Button>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {hosts.map((host) => (
            <Grid item xs={12} md={6} lg={4} key={host.id}>
              <HostStatusCard host={host} onRefresh={handleRefreshHost} />
            </Grid>
          ))}
        </Grid>
      )}
      
      {/* Generate Report Dialog */}
      <GenerateReportDialog
        open={generateDialogOpen}
        onClose={() => setGenerateDialogOpen(false)}
        onSubmit={handleGenerateReport}
        environment={environment}
      />
      
      {/* Snackbar notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MonitorPage;
