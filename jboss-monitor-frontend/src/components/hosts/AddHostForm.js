// src/components/hosts/AddHostForm.js
import React, { useState } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  TextField, 
  Alert 
} from '@mui/material';

const AddHostForm = ({ open, onClose, onSubmit, environment }) => {
  const [host, setHost] = useState('');
  const [port, setPort] = useState('');
  const [instance, setInstance] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Basic validation
    if (!host || !port || !instance) {
      setError('All fields are required');
      return;
    }

    try {
      const portNumber = parseInt(port, 10);
      if (isNaN(portNumber)) {
        setError('Port must be a valid number');
        return;
      }

      onSubmit({ host, port: portNumber, instance });
      // Reset form
      setHost('');
      setPort('');
      setInstance('');
      setError('');
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to add host');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add New Host to {environment === 'production' ? 'Production' : 'Non-Production'}</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <TextField
            autoFocus
            margin="dense"
            label="Host Name"
            type="text"
            fullWidth
            variant="outlined"
            value={host}
            onChange={(e) => setHost(e.target.value)}
            required
          />
          
          <TextField
            margin="dense"
            label="Port"
            type="number"
            fullWidth
            variant="outlined"
            value={port}
            onChange={(e) => setPort(e.target.value)}
            required
          />
          
          <TextField
            margin="dense"
            label="Instance Name"
            type="text"
            fullWidth
            variant="outlined"
            value={instance}
            onChange={(e) => setInstance(e.target.value)}
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" color="primary" variant="contained">
            Add Host
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default AddHostForm;
