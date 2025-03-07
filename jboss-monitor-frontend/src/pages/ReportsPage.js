// src/pages/ReportsPage.js
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
  Chip,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Grid
} from '@mui/material';
import {
  PictureAsPdf as PdfIcon,
  TableChart as TableChartIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getReports, generateReport, deleteReport, getReportDownloadUrl } from '../api/reports';

// Generate Report Dialog Component
const GenerateReportDialog = ({ open, onClose, onSubmit }) => {
  const [environment, setEnvironment] = useState('production');
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
      await onSubmit(environment, username, password, format);
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

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="sm" fullWidth>
      <DialogTitle>Generate Status Report</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Select the environment and enter your JBoss credentials to generate a detailed status report.
          </Typography>
          
          <FormControl fullWidth margin="dense">
            <InputLabel id="environment-label">Environment</InputLabel>
            <Select
              labelId="environment-label"
              id="environment"
              value={environment}
              label="Environment"
              onChange={(e) => setEnvironment(e.target.value)}
              disabled={loading}
            >
              <MenuItem value="production">Production</MenuItem>
              <MenuItem value="non_production">Non-Production</MenuItem>
            </Select>
          </FormControl>
          
          <TextField
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

// Delete Report Dialog
const DeleteReportDialog = ({ open, report, onClose, onConfirm }) => {
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
          Are you sure you want to delete this report? This action cannot be undone.
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

// Main Reports Page Component
const ReportsPage = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });
  
  const { token } = useAuth();
  const navigate = useNavigate();
  
  // Fetch reports on mount
  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const reportsData = await getReports(token);
        setReports(reportsData);
      } catch (err) {
        setError(err.message || 'Failed to load reports');
      } finally {
        setLoading(false);
      }
    };
    
    fetchReports();
    
    // Set up refresh interval (every 30 seconds)
    const intervalId = setInterval(() => {
      fetchReports();
    }, 30000);
    
    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, [token]);
  
  // Handle generate report
  const handleGenerateReport = async (environment, username, password, format) => {
    try {
      const result = await generateReport(token, environment, username, password, format);
      
      // Add the new report to the list
      setReports(prev => [result, ...prev]);
      
      setSnackbar({
        open: true,
        message: 'Report generation initiated',
        severity: 'success'
      });
      
      return result;
    } catch (err) {
      throw err;
    }
  };
  
  // Handle delete report
  const handleDeleteReport = async () => {
    if (!selectedReport) return;
    
    try {
      await deleteReport(token, selectedReport.id);
      
      // Remove the deleted report from the list
      setReports(prev => prev.filter(r => r.id !== selectedReport.id));
      
      setSnackbar({
        open: true,
        message: 'Report deleted successfully',
        severity: 'success'
      });
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message || 'Failed to delete report',
        severity: 'error'
      });
    }
  };
  
  // Open delete dialog
  const openDeleteDialog = (report) => {
    setSelectedReport(report);
    setDeleteDialogOpen(true);
  };
  
  // Handle download report
  const handleDownloadReport = (report) => {
    if (report.status !== 'completed') {
      setSnackbar({
        open: true,
        message: 'Report is not ready for download',
        severity: 'warning'
      });
      return;
    }
    
    // Create download URL
    const downloadUrl = getReportDownloadUrl(report.id);
    
    // Add JWT token to URL
    const url = `${downloadUrl}?token=${token}`;
    
    // Open in new tab
    window.open(url, '_blank');
  };
  
  // Close snackbar
  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };
  
  // Format report creation date
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch (e) {
      return dateString || 'Unknown';
    }
  };
  
  // Get status chip color
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'generating': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };
  
  // Get format icon
  const getFormatIcon = (format) => {
    return format === 'pdf' ? <PdfIcon /> : <TableChartIcon />;
  };

  // Render a spinner while loading
  if (loading && !reports.length) {
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
          Reports
        </Typography>
        
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setGenerateDialogOpen(true)}
        >
          Generate Report
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {reports.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 5 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Reports Yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Generate your first JBoss status report by clicking the button below.
            </Typography>
            <Button 
              variant="outlined" 
              startIcon={<AddIcon />}
              onClick={() => setGenerateDialogOpen(true)}
            >
              Generate Report
            </Button>
          </CardContent>
        </Card>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Environment</TableCell>
                <TableCell>Format</TableCell>
                <TableCell>Created At</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {reports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <StorageIcon 
                        color={report.environment === 'production' ? 'error' : 'info'} 
                        fontSize="small" 
                      />
                      <Typography>
                        {report.environment === 'production' ? 'Production' : 'Non-Production'}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getFormatIcon(report.format)}
                      <Typography>
                        {report.format.toUpperCase()}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {formatDate(report.created_at)}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={report.status.toUpperCase()} 
                      color={getStatusColor(report.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                      <Tooltip title="Download Report">
                        <span>
                          <IconButton 
                            color="primary"
                            onClick={() => handleDownloadReport(report)}
                            disabled={report.status !== 'completed'}
                          >
                            <DownloadIcon />
                          </IconButton>
                        </span>
                      </Tooltip>
                      
                      <Tooltip title="Delete Report">
                        <IconButton 
                          color="error"
                          onClick={() => openDeleteDialog(report)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      
      {/* Dialogs */}
      <GenerateReportDialog
        open={generateDialogOpen}
        onClose={() => setGenerateDialogOpen(false)}
        onSubmit={handleGenerateReport}
      />
      
      <DeleteReportDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteReport}
        report={selectedReport}
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

export default ReportsPage;
