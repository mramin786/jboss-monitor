import React from 'react';
import { Typography, Box, Paper, Button } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';

const ReportDetailsPage = () => {
  const { reportId } = useParams();
  const navigate = useNavigate();

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Report Details
      </Typography>
      
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6">
          Report ID: {reportId}
        </Typography>
        
        <Typography variant="body1" sx={{ mt: 2 }}>
          Detailed information about the selected report will be displayed here.
        </Typography>
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
          <Button 
            variant="outlined"
            onClick={() => navigate('/reports')}
          >
            Back to Reports
          </Button>
          
          <Button 
            variant="contained"
            color="primary"
          >
            Download Report
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default ReportDetailsPage;
