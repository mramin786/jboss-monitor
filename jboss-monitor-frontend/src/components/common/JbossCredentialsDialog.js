// src/components/common/JbossCredentialsDialog.js
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert,
  CircularProgress
} from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';
import { storeJbossCredentials } from '../../api/auth';

const JbossCredentialsDialog = ({ open, environment, onClose }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const { token } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      await storeJbossCredentials(token, environment, username, password);
      setSuccess(true);

      // Reset form
      setTimeout(() => {
        if (open) {
          setUsername('');
          setPassword('');
          setSuccess(false);
          onClose();
        }
      }, 1500);
    } catch (err) {
      setError(err.message || 'Failed to store credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setUsername('');
    setPassword('');
    setError('');
    setSuccess(false);
    onClose();
  };

  const envName = environment === 'production' ? 'Production' : 'Non-Production';

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="sm" fullWidth>
      <DialogTitle>{envName} JBoss Credentials</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Credentials stored successfully!
            </Alert>
          )}

          <TextField
            autoFocus
            margin="dense"
            id="username"
            label="JBoss Username"
            type="text"
            fullWidth
            variant="outlined"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={loading || success}
          />

          <TextField
            margin="dense"
            id="password"
            label="JBoss Password"
            type="password"
            fullWidth
            variant="outlined"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading || success}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancel} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading || success}
            startIcon={loading && <CircularProgress size={20} />}
          >
            {loading ? 'Saving...' : 'Save Credentials'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default JbossCredentialsDialog;
