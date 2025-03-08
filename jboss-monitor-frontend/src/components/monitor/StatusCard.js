// src/components/monitor/StatusCard.js
import React from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  LinearProgress 
} from '@mui/material';
import StatusBadge from '../common/StatusBadge';

const StatusCard = ({ host }) => {
  const calculateUpPercentage = (items) => {
    if (!items || items.length === 0) return 0;
    const upItems = items.filter(item => item.status === 'up');
    return (upItems.length / items.length) * 100;
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">{host.host}</Typography>
          <StatusBadge status={host.status?.instance_status || 'unknown'} />
        </Box>
        
        <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
          {host.instance} | Port: {host.port}
        </Typography>
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2">Datasources</Typography>
          <LinearProgress 
            variant="determinate" 
            value={calculateUpPercentage(host.status?.datasources)}
            color="primary"
            sx={{ mt: 1 }}
          />
        </Box>
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2">Deployments</Typography>
          <LinearProgress 
            variant="determinate" 
            value={calculateUpPercentage(host.status?.deployments)}
            color="secondary"
            sx={{ mt: 1 }}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

export default StatusCard;
