import React from 'react';
import { 
  Box, 
  Typography, 
  List, 
  ListItem, 
  ListItemText, 
  Paper 
} from '@mui/material';
import { Storage as StorageIcon } from '@mui/icons-material';
import StatusBadge from '../common/StatusBadge';

const DatasourceStatus = ({ datasources }) => {
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
        <StorageIcon sx={{ mr: 2 }} />
        <Typography variant="h6">
          Datasource Status
        </Typography>
      </Box>
      
      {datasources && datasources.length > 0 ? (
        <List dense>
          {datasources.map((ds, index) => (
            <ListItem key={index}>
              <ListItemText 
                primary={ds.name}
                secondary={ds.type}
              />
              <StatusBadge 
                status={ds.status} 
                severity={getSeverityColor(ds.status)} 
              />
            </ListItem>
          ))}
        </List>
      ) : (
        <Typography variant="body2" color="textSecondary">
          No datasources found
        </Typography>
      )}
    </Paper>
  );
};

export default DatasourceStatus;
