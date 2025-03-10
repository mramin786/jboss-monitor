// src/components/reports/CompareReportsDialog.js
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Typography,
  Box,
  Grid
} from '@mui/material';
import { CompareArrows as CompareArrowsIcon } from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { getReports, compareReports } from '../../api/reports';

const CompareReportsDialog = ({ open, onClose, onCompare }) => {
  const [report1, setReport1] = useState('');
  const [report2, setReport2] = useState('');
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState('');
  
  const { token } = useAuth();
  
  // Fetch available reports
  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      try {
        const data = await getReports();
        
        // Filter out only completed reports
        const completedReports = data.filter(r => r.status === 'completed' && r.type !== 'comparison');
        
        setReports(completedReports);
        setError('');
      } catch (err) {
        setError('Failed to fetch reports: ' + (err.message || 'Unknown error'));
      } finally {
        setLoading(false);
      }
    };
    
    if (open) {
      fetchReports();
    }
  }, [open]);
  
  const handleCompare = async () => {
    if (!report1 || !report2) {
      setError('Please select two reports to compare');
      return;
    }
    
    if (report1 === report2) {
      setError('Please select two different reports');
      return;
    }
    
    setError('');
    setComparing(true);
    
    try {
      const result = await compareReports(token, report1, report2);
      
      // Call the parent's onCompare callback
      onCompare(result);
      
      // Reset the form
      handleReset();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to compare reports');
    } finally {
      setComparing(false);
    }
  };
  
  const handleReset = () => {
    setReport1('');
    setReport2('');
    setError('');
  };
  
  const handleCancel = () => {
    handleReset();
    onClose();
  };

  // Format date for display
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch (e) {
      return dateString || 'Unknown';
    }
  };
  
  // Get report options for dropdowns
  const getReportOptions = () => {
    return reports.map(report => ({
      value: report.id,
      label: `${report.environment === 'production' ? 'Production' : 'Non-Production'} - ${formatDate(report.created_at)}`
    }));
  };
  
  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="md" fullWidth>
      <DialogTitle>Compare Reports</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Select two reports to compare and identify changes in status, datasources, and deployments.
        </Typography>
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        ) : reports.length < 2 ? (
          <Alert severity="warning" sx={{ mb: 2 }}>
            You need at least two completed reports to perform a comparison.
          </Alert>
        ) : (
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={5}>
              <FormControl fullWidth>
                <InputLabel id="report1-label">First Report (Older)</InputLabel>
                <Select
                  labelId="report1-label"
                  value={report1}
                  label="First Report (Older)"
                  onChange={(e) => setReport1(e.target.value)}
                  disabled={comparing}
                >
                  {getReportOptions().map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={2} sx={{ textAlign: 'center' }}>
              <CompareArrowsIcon fontSize="large" color="action" />
            </Grid>
            
            <Grid item xs={12} md={5}>
              <FormControl fullWidth>
                <InputLabel id="report2-label">Second Report (Newer)</InputLabel>
                <Select
                  labelId="report2-label"
                  value={report2}
                  label="Second Report (Newer)"
                  onChange={(e) => setReport2(e.target.value)}
                  disabled={comparing}
                >
                  {getReportOptions().map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        )}
        
        <Box sx={{ my: 3 }}>
          <Divider />
        </Box>
        
        <Typography variant="body2" color="text.secondary">
          The comparison will analyze both reports and highlight differences in:
        </Typography>
        <ul>
          <li>
            <Typography variant="body2" color="text.secondary">
              Host status changes (UP/DOWN)
            </Typography>
          </li>
          <li>
            <Typography variant="body2" color="text.secondary">
              Datasource status changes
            </Typography>
          </li>
          <li>
            <Typography variant="body2" color="text.secondary">
              Deployment status changes
            </Typography>
          </li>
          <li>
            <Typography variant="body2" color="text.secondary">
              Added or removed hosts, datasources, and deployments
            </Typography>
          </li>
        </ul>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancel} disabled={comparing}>
          Cancel
        </Button>
        <Button 
          variant="contained" 
          onClick={handleCompare}
          disabled={comparing || reports.length < 2 || !report1 || !report2}
          startIcon={comparing ? <CircularProgress size={20} /> : <CompareArrowsIcon />}
        >
          {comparing ? 'Comparing...' : 'Compare Reports'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CompareReportsDialog;
