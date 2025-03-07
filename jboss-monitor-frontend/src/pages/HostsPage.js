// src/pages/HostsPage.js
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  Snackbar,
  Tabs,
  Tab,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  CloudUpload as CloudUploadIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import StatusBadge from '../components/common/StatusBadge';
import { getHosts, addHost, addHostsBulk, parseBulkInput, deleteHost } from '../api/hosts';
import { getMonitorStatus, checkHost } from '../api/monitor';

// Add Host Dialog Component
const AddHostDialog = ({ open, onClose, onSubmit, environment }) => {
  const [host, setHost] = useState('');
  const [port, setPort] = useState('');
  const [instance, setInstance] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      // Validate port is a number
      const portNum = parseInt(port, 10);
      if (isNaN(portNum)) {
        throw new Error('Port must be a valid number');
      }
      
      // Submit host data
      await onSubmit({ host, port: portNum, instance });
      
      // Reset form and close
      handleReset();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to add host');
    } finally {
      setLoading(false);
    }
  };
  
  const handleReset = () => {
    setHost('');
    setPort('');
    setInstance('');
    setError('');
  };
  
  const handleCancel = () => {
    handleReset();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="sm" fullWidth>
      <DialogTitle>Add New Host to {environment === 'production' ? 'Production' : 'Non-Production'}</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <TextField
            autoFocus
            margin="dense"
            id="host"
            label="Host Name"
            type="text"
            fullWidth
            variant="outlined"
            value={host}
            onChange={(e) => setHost(e.target.value)}
            required
            disabled={loading}
            placeholder="e.g., ftc-lbjbsapp211"
          />
          
          <TextField
            margin="dense"
            id="port"
            label="Port"
            type="number"
            fullWidth
            variant="outlined"
            value={port}
            onChange={(e) => setPort(e.target.value)}
            required
            disabled={loading}
            placeholder="e.g., 9990"
          />
          
          <TextField
            margin="dense"
            id="instance"
            label="JVM Instance Name"
            type="text"
            fullWidth
            variant="outlined"
            value={instance}
            onChange={(e) => setInstance(e.target.value)}
            required
            disabled={loading}
            placeholder="e.g., DEV_ABC_01"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancel} disabled={loading}>
            Cancel
          </Button>
          <Button 
            type="submit" 
            variant="contained" 
            disabled={loading}
            startIcon={loading && <CircularProgress size={20} />}
          >
            {loading ? 'Adding...' : 'Add Host'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

// Bulk Import Dialog Component
const BulkImportDialog = ({ open, onClose, onSubmit, environment }) => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState('');
  const [parsedHosts, setParsedHosts] = useState([]);
  const [invalidLines, setInvalidLines] = useState([]);
  
  const { token } = useAuth();
  
  const handleParse = async () => {
    setError('');
    setParsing(true);
    
    try {
      const result = await parseBulkInput(token, environment, input);
      setParsedHosts(result.parsed_hosts);
      setInvalidLines(result.invalid_lines);
    } catch (err) {
      setError(err.message || 'Failed to parse input');
    } finally {
      setParsing(false);
    }
  };
  
  const handleSubmit = async () => {
    if (parsedHosts.length === 0) {
      setError('No valid hosts to import');
      return;
    }
    
    setError('');
    setLoading(true);
    
    try {
      await onSubmit(parsedHosts);
      handleReset();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to import hosts');
    } finally {
      setLoading(false);
    }
  };
  
  const handleReset = () => {
    setInput('');
    setParsedHosts([]);
    setInvalidLines([]);
    setError('');
  };
  
  const handleCancel = () => {
    handleReset();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="md" fullWidth>
      <DialogTitle>Bulk Import Hosts to {environment === 'production' ? 'Production' : 'Non-Production'}</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Enter or paste host information in the format: <code>$host $port $jvm</code> (one per line)
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
          Example: <code>ftc-lbjbsapp211 9990 DEV_ABC_01</code>
        </Typography>
        
        <TextField
          autoFocus
          margin="dense"
          id="bulkInput"
          label="Bulk Host Input"
          multiline
          rows={8}
          fullWidth
          variant="outlined"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading || parsing}
          placeholder="ftc-lbjbsapp211 9990 DEV_ABC_01&#10;ftc-lbjbsapp212 9990 DEV_ABC_02&#10;ftc-lbjbsapp213 9990 DEV_ABC_03"
        />
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1, mb: 2 }}>
          <Button 
            variant="outlined" 
            onClick={handleParse}
            disabled={!input || loading || parsing}
            startIcon={parsing && <CircularProgress size={20} />}
          >
            {parsing ? 'Parsing...' : 'Parse Input'}
          </Button>
        </Box>
        
        {parsedHosts.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2">
              {parsedHosts.length} Valid Host{parsedHosts.length !== 1 ? 's' : ''}
            </Typography>
            
            <TableContainer component={Paper} sx={{ mt: 1, maxHeight: 200 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Host</TableCell>
                    <TableCell>Port</TableCell>
                    <TableCell>Instance</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {parsedHosts.map((host, index) => (
                    <TableRow key={index}>
                      <TableCell>{host.host}</TableCell>
                      <TableCell>{host.port}</TableCell>
                      <TableCell>{host.instance}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
        
        {invalidLines.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" color="error">
              {invalidLines.length} Invalid Line{invalidLines.length !== 1 ? 's' : ''}
            </Typography>
            
            <TableContainer component={Paper} sx={{ mt: 1, maxHeight: 200 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Line</TableCell>
                    <TableCell>Content</TableCell>
                    <TableCell>Reason</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {invalidLines.map((line, index) => (
                    <TableRow key={index}>
                      <TableCell>{line.line}</TableCell>
                      <TableCell>{line.content}</TableCell>
                      <TableCell>{line.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancel} disabled={loading}>
          Cancel
        </Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          disabled={loading || parsedHosts.length === 0}
          startIcon={loading && <CircularProgress size={20} />}
        >
          {loading ? 'Importing...' : 'Import Hosts'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Delete Host Dialog
const DeleteHostDialog = ({ open, host, onClose, onConfirm }) => {
  const [loading, setLoading] = useState(false);
  
  const handleDelete = async () => {
    setLoading(true);
    
    try {
      await onConfirm();
      onClose();
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs">
      <DialogTitle>Confirm Delete</DialogTitle>
      <DialogContent>
        <Typography>
          Are you sure you want to delete the host <strong>{host?.host}</strong> with instance <strong>{host?.instance}</strong>?
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button 
          color="error" 
          onClick={handleDelete}
          disabled={loading}
          startIcon={loading && <CircularProgress size={20} />}
        >
          {loading ? 'Deleting...' : 'Delete'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Main Hosts Page Component
const HostsPage = ({ environment }) => {
  const [hosts, setHosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [addHostDialogOpen, setAddHostDialogOpen] = useState(false);
  const [bulkImportDialogOpen, setBulkImportDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedHost, setSelectedHost] = useState(null);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });
  const [tabValue, setTabValue] = useState(0);
  
  const { token } = useAuth();
  const navigate = useNavigate();
  
  const envTitle = environment === 'production' ? 'Production' : 'Non-Production';
  
  // Fetch hosts on mount and when environment changes
  useEffect(() => {
    const fetchHosts = async () => {
      setLoading(true);
      setError(null);
      
      try {
        let hostsData;
        
        if (tabValue === 0) {
          // Fetch hosts with status
          hostsData = await getMonitorStatus(token, environment);
        } else {
          // Fetch hosts without status
          hostsData = await getHosts(token, environment);
        }
        
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
      if (tabValue === 0) { // Only auto-refresh on the status tab
        fetchHosts();
      }
    }, 30000);
    
    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, [token, environment, tabValue, envTitle]);
  
  // Handle add host
  const handleAddHost = async (hostData) => {
    const result = await addHost(token, environment, hostData);
    setHosts(prev => [...prev, result]);
    setSnackbar({
      open: true,
      message: 'Host added successfully',
      severity: 'success'
    });
  };
  
  // Handle bulk import
  const handleBulkImport = async (hostsData) => {
    const result = await addHostsBulk(token, environment, hostsData);
    
    if (result.added.length > 0) {
      setHosts(prev => [...prev, ...result.added]);
      setSnackbar({
        open: true,
        message: `${result.added.length} hosts added successfully`,
        severity: 'success'
      });
    }
    
    if (result.rejected.length > 0) {
      console.warn('Some hosts were rejected:', result.rejected);
    }
  };
  
  // Handle delete host
  const handleDeleteHost = async () => {
    if (!selectedHost) return;
    
    await deleteHost(token, environment, selectedHost.id);
    setHosts(prev => prev.filter(h => h.id !== selectedHost.id));
    setSnackbar({
      open: true,
      message: 'Host deleted successfully',
      severity: 'success'
    });
  };
  
  // Handle check host status
  const handleCheckHost = async (host) => {
    try {
      await checkHost(token, environment, host.id);
      setSnackbar({
        open: true,
        message: 'Status check initiated',
        severity: 'info'
      });
      
      // Refresh hosts after a short delay
      setTimeout(() => {
        getMonitorStatus(token, environment)
          .then(data => setHosts(data))
          .catch(err => console.error('Failed to refresh hosts:', err));
      }, 2000);
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message || 'Failed to check host status',
        severity: 'error'
      });
    }
  };
  
  // Open delete dialog
  const openDeleteDialog = (host) => {
    setSelectedHost(host);
    setDeleteDialogOpen(true);
  };
  
  // Close snackbar
  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };
  
  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
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
          {envTitle} Hosts
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<CloudUploadIcon />}
            onClick={() => setBulkImportDialogOpen(true)}
          >
            Bulk Import
          </Button>
          
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddHostDialogOpen(true)}
          >
            Add Host
          </Button>
        </Box>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label="Status View" />
          <Tab label="Management View" />
        </Tabs>
      </Paper>
      
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Host</TableCell>
                <TableCell>Port</TableCell>
                <TableCell>Instance</TableCell>
                {tabValue === 0 && (
                  <>
                    <TableCell>Status</TableCell>
                    <TableCell>Last Check</TableCell>
                    <TableCell>Datasources</TableCell>
                    <TableCell>Deployments</TableCell>
                  </>
                )}
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {hosts.length === 0 ? (
                <TableRow>
                  <TableCell 
                    colSpan={tabValue === 0 ? 8 : 4} 
                    align="center" 
                    sx={{ py: 3 }}
                  >
                    <Typography variant="body2" color="text.secondary">
                      No hosts found
                    </Typography>
                    <Button 
                      variant="text" 
                      startIcon={<AddIcon />}
                      onClick={() => setAddHostDialogOpen(true)}
                      sx={{ mt: 1 }}
                    >
                      Add Host
                    </Button>
                  </TableCell>
                </TableRow>
              ) : (
                hosts.map((host) => (
                  <TableRow key={host.id}>
                    <TableCell>{host.host}</TableCell>
                    <TableCell>{host.port}</TableCell>
                    <TableCell>{host.instance}</TableCell>
                    
                    {tabValue === 0 && (
                      <>
                        <TableCell>
                          <StatusBadge status={host.status?.instance_status || 'unknown'} />
                        </TableCell>
                        <TableCell>
                          {host.status?.last_check ? (
                            new Date(host.status.last_check).toLocaleString()
                          ) : (
                            'Never'
                          )}
                        </TableCell>
                        <TableCell>
                          {host.status?.datasources?.length || 0}
                        </TableCell>
                        <TableCell>
                          {host.status?.deployments?.length || 0}
                        </TableCell>
                      </>
                    )}
                    
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        {tabValue === 0 && (
                          <Tooltip title="Check Status">
                            <IconButton 
                              color="primary"
                              onClick={() => handleCheckHost(host)}
                            >
                              <RefreshIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        <Tooltip title="View Details">
                          <IconButton 
                            color="info"
                            onClick={() => navigate(`/${environment}/hosts/${host.id}`)}
                          >
                            <VisibilityIcon />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Delete Host">
                          <IconButton 
                            color="error"
                            onClick={() => openDeleteDialog(host)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
      
      {/* Dialogs */}
      <AddHostDialog
        open={addHostDialogOpen}
        onClose={() => setAddHostDialogOpen(false)}
        onSubmit={handleAddHost}
        environment={environment}
      />
      
      <BulkImportDialog
        open={bulkImportDialogOpen}
        onClose={() => setBulkImportDialogOpen(false)}
        onSubmit={handleBulkImport}
        environment={environment}
      />
      
      <DeleteHostDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteHost}
        host={selectedHost}
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

export default HostsPage;
