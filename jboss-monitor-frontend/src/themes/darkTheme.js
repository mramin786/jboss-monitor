// src/themes/darkTheme.js
import { createTheme } from '@mui/material/styles';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#64b5f6', // Light blue
      light: '#9be7ff',
      dark: '#2286c3',
      contrastText: '#000000',
    },
    secondary: {
      main: '#1e88e5', // Darker blue
      light: '#6ab7ff',
      dark: '#005cb2',
      contrastText: '#ffffff',
    },
    background: {
      default: '#0a1929', // Very dark blue
      paper: '#102a43', // Dark blue
    },
    text: {
      primary: '#ffffff',
      secondary: '#b3e5fc', // Light blue text
    },
    error: {
      main: '#f44336', // Red
    },
    warning: {
      main: '#ff9800', // Amber
    },
    info: {
      main: '#2196f3', // Blue
    },
    success: {
      main: '#4caf50', // Green
    },
    status: {
      up: '#4caf50', // Green
      down: '#f44336', // Red
      pending: '#ff9800', // Amber
      unknown: '#9e9e9e', // Gray
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiAppBar: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          backgroundColor: '#102a43', // Dark blue
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#0a1929', // Very dark blue
          border: 'none',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '8px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          boxShadow: '0 5px 10px rgba(0, 0, 0, 0.2)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '8px',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 'bold',
          backgroundColor: 'rgba(16, 42, 67, 0.5)', // Slightly lighter dark blue
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:nth-of-type(odd)': {
            backgroundColor: 'rgba(16, 42, 67, 0.2)', // Very light dark blue
          },
          '&:hover': {
            backgroundColor: 'rgba(16, 42, 67, 0.5)', // Light dark blue
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

export default darkTheme;
