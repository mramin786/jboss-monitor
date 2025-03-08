// src/components/common/StatusBadge.js
import React from 'react';
import { Chip } from '@mui/material';
import {
  CheckCircleOutline,
  ErrorOutline,
  HelpOutline,
  HourglassEmpty
} from '@mui/icons-material';

const StatusBadge = ({ status, size = 'medium' }) => {
  const statusLower = status?.toLowerCase() || 'unknown';

  const getStatusConfig = () => {
    switch (statusLower) {
      case 'up':
        return {
          label: 'UP',
          color: 'success',
          icon: <CheckCircleOutline />
        };
      case 'down':
        return {
          label: 'DOWN',
          color: 'error',
          icon: <ErrorOutline />
        };
      case 'pending':
        return {
          label: 'PENDING',
          color: 'warning',
          icon: <HourglassEmpty />
        };
      default:
        return {
          label: 'UNKNOWN',
          color: 'default',
          icon: <HelpOutline />
        };
    }
  };

  const { label, color, icon } = getStatusConfig();

  return (
    <Chip
      label={label}
      color={color}
      size={size}
      icon={icon}
      variant="outlined"
    />
  );
};

export default StatusBadge;
