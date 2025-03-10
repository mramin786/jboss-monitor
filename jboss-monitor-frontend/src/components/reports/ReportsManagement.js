// src/components/reports/ReportsManagement.js
import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  CircularProgress,
  Alert,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider
} from '@mui/material';
import {
  DeleteSweep as DeleteSweepIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../api/apiClient';
import { cleanupReports } from '../../api/reports';

const ReportsManagement = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [environment, setEnvironment] = useState('all');
  const [maxReports, setMaxReports] = useState(10);
  
  const { currentUser } = useAuth();
  
  // Only allow admins to see this component
  if (currentUser?.role !== 'admin') {
    return null;
  }
  
  const handleCleanup = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      // Use the cleanupReports function from api/reports
      const response = await cleanupReports(
        environment === 'all' ? null : environment, 
        maxReports
      );
      
      setSuccess(`Cleanup successful: ${response.deleted_count} reports deleted`);
    } catch (err) {
      setError(err.message || 'Failed to run cleanup');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Paper sx={{ p: 3, mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Reports Management
      </Typography>
      
      <Divider sx={{ mb: 2 }} />
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}
      
      <Box sx={{ mb: 2 }}>
        <Alert severity="info" icon={<InfoIcon />}>
          The system automatically keeps only the most recent reports per environment.
          Use this function to manually trigger cleanup or adjust the limit.
        </Alert>
      </Box>
      
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel id="environment-select-label">Environment</InputLabel>
          <Select
            labelId="environment-select-label"
            value={environment}
            label="Environment"
            onChange={(e) => setEnvironment(e.target.value)}
            disabled={loading}
          >
            <MenuItem value="all">All Environments</MenuItem>
            <MenuItem value="production">Production</MenuItem>
            <MenuItem value="non_production">Non-Production</MenuItem>
          </Select>
        </FormControl>
        
        <TextField
          label="Max Reports"
          type="number"
          value={maxReports}
          onChange={(e) => setMaxReports(parseInt(e.target.value, 10))}
          InputProps={{ inputProps: { min: 1, max: 100 } }}
          disabled={loading}
          sx={{ width: 150 }}
        />
        
        <Button
          variant="contained"
          color="warning"
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <DeleteSweepIcon />}
          onClick={handleCleanup}
          disabled={loading}
        >
          {loading ? 'Cleaning...' : 'Clean Old Reports'}
        </Button>
      </Box>
      
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        This will keep the {maxReports} most recent reports
        {environment !== 'all' ? ` for the ${environment.replace('_', '-')} environment` : ' for each environment'}.
        Older reports will be permanently deleted.
      </Typography>
    </Paper>
  );
};

export default ReportsManagement;
