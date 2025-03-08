
// src/components/common/LoadingSpinner.js
import React from 'react';
import { Box, CircularProgress } from '@mui/material';

const LoadingSpinner = ({ fullScreen = false }) => {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: fullScreen ? '100vh' : '100%',
        width: '100%'
      }}
    >
      <CircularProgress color="primary" />
    </Box>
  );
};
