// src/components/common/Footer.js
import React from 'react';
import { Box, Typography, Link } from '@mui/material';

const Footer = () => {
  return (
    <Box 
      sx={{ 
        py: 2, 
        textAlign: 'center', 
        backgroundColor: 'background.paper' 
      }}
    >
      <Typography variant="body2" color="text.secondary">
        © {new Date().getFullYear()} JBoss Monitor. 
        All Rights Reserved.
      </Typography>
      <Typography variant="caption" color="text.secondary">
        <Link href="#" color="inherit">
          Privacy Policy
        </Link>{' | '}
        <Link href="#" color="inherit">
          Terms of Service
        </Link>
      </Typography>
    </Box>
  );
};

export default Footer;
