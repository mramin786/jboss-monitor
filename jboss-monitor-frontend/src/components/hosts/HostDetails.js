// src/components/hosts/HostDetails.js
import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Divider, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Button,
  CircularProgress
} from '@mui/material';
import { useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getMonitorStatus } from '../../api/monitor';
import StatusBadge from '../common/StatusBadge';

const HostDetails = () => {
  const { environment, hostId } = useParams();
  const { token } = useAuth();
  const [hostDetails, setHostDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHostDetails = async () => {
      try {
        const hosts = await getMonitorStatus(token, environment);
        const host = hosts.find(h => h.id === hostId);
        
        if (!host) {
          throw new Error('Host not found');
        }
        
        setHostDetails(host);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHostDetails();
  }, [token, environment, hostId]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Host Details: {hostDetails.host}
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Basic Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Host Name
                </Typography>
                <Typography>{hostDetails.host}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Port
                </Typography>
                <Typography>{hostDetails.port}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Instance
                </Typography>
                <Typography>{hostDetails.instance}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
	  // Continuing from previous code
                  Status
                </Typography>
                <StatusBadge status={hostDetails.status?.instance_status || 'unknown'} />
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Datasources
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {hostDetails.status?.datasources?.map((ds, index) => (
                    <TableRow key={index}>
                      <TableCell>{ds.name}</TableCell>
                      <TableCell>{ds.type}</TableCell>
                      <TableCell>
                        <StatusBadge status={ds.status} size="small" />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Deployments
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {hostDetails.status?.deployments?.map((dep, index) => (
                    <TableRow key={index}>
                      <TableCell>{dep.name}</TableCell>
                      <TableCell>
                        <StatusBadge status={dep.status} size="small" />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default HostDetails;
