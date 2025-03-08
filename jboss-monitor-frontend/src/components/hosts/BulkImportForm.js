// src/components/hosts/BulkImportForm.js
import React, { useState } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  TextField, 
  Typography, 
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';

const BulkImportForm = ({ open, onClose, onSubmit, environment }) => {
  const [input, setInput] = useState('');
  const [parsedHosts, setParsedHosts] = useState([]);
  const [invalidLines, setInvalidLines] = useState([]);

  const parseInput = () => {
    const lines = input.trim().split('\n');
    const validHosts = [];
    const invalid = [];

    lines.forEach((line, index) => {
      const parts = line.trim().split(/\s+/);
      if (parts.length === 3) {
        try {
          const port = parseInt(parts[1], 10);
          if (isNaN(port)) throw new Error('Invalid port');
          
          validHosts.push({
            host: parts[0],
            port: port,
            instance: parts[2]
          });
        } catch (err) {
          invalid.push({
            line: index + 1,
            content: line,
            reason: err.message || 'Invalid format'
          });
        }
      } else {
        invalid.push({
          line: index + 1,
          content: line,
          reason: 'Invalid format: Expected "host port instance"'
        });
      }
    });

    setParsedHosts(validHosts);
    setInvalidLines(invalid);
  };

  const handleSubmit = () => {
    onSubmit(parsedHosts);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Bulk Import Hosts to {environment}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" sx={{ mb: 2 }}>
          Enter hosts in the format: host port instance (one per line)
        </Typography>
        
        <TextField
          multiline
          rows={6}
          fullWidth
          variant="outlined"
          placeholder="ftc-lbjbsapp01 9990 DEV_APP_01
ftc-lbjbsapp02 9990 DEV_APP_02"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        
        <Button 
          variant="outlined" 
          sx={{ mt: 2 }}
          onClick={parseInput}
        >
          Parse Input
        </Button>
        
        {parsedHosts.length > 0 && (
          <>
            <Typography variant="h6" sx={{ mt: 2 }}>
              Valid Hosts ({parsedHosts.length})
            </Typography>
            <TableContainer component={Paper} sx={{ mt: 1 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Host</TableCell>
                    <TableCell>Port</TableCell>
                    <TableCell>Instance</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {parsedHosts.map((host, index) => (
                    <TableRow key={index}>
                      <TableCell>{host.host}</TableCell>
                      <TableCell>{host.port}</TableCell>
                      <TableCell>{host.instance}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
        
        {invalidLines.length > 0 && (
          <>
            <Typography variant="h6" color="error" sx={{ mt: 2 }}>
              Invalid Lines ({invalidLines.length})
            </Typography>
            <TableContainer component={Paper} sx={{ mt: 1 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Line</TableCell>
                    <TableCell>Content</TableCell>
                    <TableCell>Reason</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {invalidLines.map((line, index) => (
                    <TableRow key={index}>
                      <TableCell>{line.line}</TableCell>
                      <TableCell>{line.content}</TableCell>
                      <TableCell color="error">{line.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button 
          variant="contained" 
          color="primary"
          onClick={handleSubmit}
          disabled={parsedHosts.length === 0}
        >
          Import {parsedHosts.length} Hosts
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default BulkImportForm;
