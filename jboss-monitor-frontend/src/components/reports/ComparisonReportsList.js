// src/components/reports/ComparisonReportsList.js
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Tab,
  Tabs
} from '@mui/material';
import {
  Download as DownloadIcon,
  Delete as DeleteIcon,
  CompareArrows as CompareArrowsIcon
} from '@mui/icons-material';

import { getComparisons, downloadComparison } from '../../api/reports';

const ComparisonReportsList = ({ onDelete }) => {
  const [comparisons, setComparisons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch comparisons on mount
  useEffect(() => {
    const fetchComparisons = async () => {
      setLoading(true);
      try {
        const data = await getComparisons();
        if (Array.isArray(data)) {
          setComparisons(data);
          setError(null);
        } else {
          // Handle unexpected response format
          console.warn("Unexpected comparisons data format:", data);
          setError("Received invalid data format from server");
        }
      } catch (err) {
        console.error("Error in fetchComparisons:", err);
        setError(err.message || 'Failed to load comparison reports');
      } finally {
        setLoading(false);
      }
    };

    fetchComparisons();
  }, []);

  // Handle download report
  const handleDownload = async (comparison) => {
    if (comparison.status !== 'completed') {
      return;
    }
    
    try {
      await downloadComparison(comparison.id);
    } catch (err) {
      console.error("Download error:", err);
    }
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

  // Check if we have comparison reports
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (comparisons.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mt: 4 }}>
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <CompareArrowsIcon sx={{ mr: 1 }} />
        <Typography variant="h6">
          Comparison Reports
        </Typography>
      </Box>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Environment</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {comparisons.map((comparison) => (
              <TableRow key={comparison.id}>
                <TableCell>
                  {comparison.environment === 'production' ? 'Production' : 'Non-Production'}
                </TableCell>
                <TableCell>{formatDate(comparison.created_at)}</TableCell>
                <TableCell>
                  <Chip 
                    label={comparison.status.toUpperCase()} 
                    color={comparison.status === 'completed' ? 'success' : 'warning'}
                    size="small"
                    icon={comparison.status === 'generating' ? <CircularProgress size={16} color="inherit" /> : undefined}
                  />
                </TableCell>
                <TableCell align="right">
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Tooltip title="Download Comparison">
                      <span>
                        <IconButton 
                          color="primary"
                          onClick={() => handleDownload(comparison)}
                          disabled={comparison.status !== 'completed'}
                        >
                          <DownloadIcon />
                        </IconButton>
                      </span>
                    </Tooltip>
                    <Tooltip title="Delete Comparison">
                      <IconButton 
                        color="error"
                        onClick={() => onDelete(comparison)}
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
    </Box>
  );
};

export default ComparisonReportsList;
