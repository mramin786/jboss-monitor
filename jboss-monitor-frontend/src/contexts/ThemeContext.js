import React, { createContext, useState, useContext } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import darkTheme from '../themes/darkTheme';

const ThemeContext = createContext();

export const ThemeContextProvider = ({ children }) => {
  const [theme, setTheme] = useState(darkTheme);

  const toggleTheme = () => {
    setTheme(prevTheme => 
      prevTheme.palette.mode === 'dark' 
        ? createTheme({ palette: { mode: 'light' } }) 
        : darkTheme
    );
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeContextProvider');
  }
  return context;
};

export default ThemeContext;
