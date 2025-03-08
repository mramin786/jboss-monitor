// src/components/monitor/DeploymentStatus.js
import React from 'react';
import { 
  Box, 
  Typography, 
  List, 
  ListItem, 
  ListItemText, 
  Paper 
} from '@mui/material';
import { Web as WebIcon } from '@mui/icons-material';
import StatusBadge from '../common/StatusBadge';

const DeploymentStatus = ({ deployments }) => {
  const getSeverityColor = (status) => {
    switch (status) {
      case 'up': return 'success';
      case 'down': return 'error';
      default: return 'default';
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <WebIcon sx={{ mr: 2 }} />
        <Typography variant="h6">
          Deployment Status
        </Typography>
      </Box>
      
      {deployments && deployments.length > 0 ? (
        <List dense>
          {deployments.map((deployment, index) => (
            <ListItem key={index}>
              <ListItemText 
                primary={deployment.name}
              />
              <StatusBadge 
                status={deployment.status} 
                severity={getSeverityColor(deployment.status)} 
              />
            </ListItem>
          ))}
        </List>
      ) : (
        <Typography variant="body2" color="textSecondary">
          No deployments found
        </Typography>
      )}
    </Paper>
  );
};

export default DeploymentStatus;
