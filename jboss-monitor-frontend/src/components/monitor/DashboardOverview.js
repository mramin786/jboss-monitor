// src/components/monitor/DashboardOverview.js
import React from 'react';
import { 
  Box, 
  Grid, 
  Typography, 
  Paper, 
  Divider 
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Storage as StorageIcon,
  DataUsage as DataUsageIcon
} from '@mui/icons-material';

const DashboardOverview = ({ productionStats, nonProductionStats }) => {
  const renderStatCard = (title, icon, stats) => (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        {icon}
        <Typography variant="h6" sx={{ ml: 2 }}>
          {title}
        </Typography>
      </Box>
      <Divider sx={{ mb: 2 }} />
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Typography variant="body2" color="textSecondary">
            Total Hosts
          </Typography>
          <Typography variant="h5">{stats.totalHosts}</Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="textSecondary">
            Up Hosts
          </Typography>
          <Typography variant="h5" color="success.main">
            {stats.upHosts}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="textSecondary">
            Total Datasources
          </Typography>
          <Typography variant="h5">{stats.totalDatasources}</Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="textSecondary">
            Up Datasources
          </Typography>
          <Typography variant="h5" color="success.main">
            {stats.upDatasources}
          </Typography>
        </Grid>
      </Grid>
    </Paper>
  );

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        {renderStatCard(
          'Production Environment', 
          <ComputerIcon color="error" />, 
          productionStats
        )}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderStatCard(
          'Non-Production Environment', 
          <StorageIcon color="info" />, 
          nonProductionStats
        )}
      </Grid>
    </Grid>
  );
};

export default DashboardOverview;
