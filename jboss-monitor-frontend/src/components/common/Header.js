// src/components/common/Header.js
import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Box,
  Menu,
  MenuItem,
  Divider,
  Tooltip
} from '@mui/material';
import {
  Menu as MenuIcon,
  AccountCircle,
  Refresh as RefreshIcon,
  Key as KeyIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import JbossCredentialsDialog from './JbossCredentialsDialog';

const Header = ({ toggleSidebar }) => {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  const [anchorEl, setAnchorEl] = useState(null);
  const [credentialsDialog, setCredentialsDialog] = useState({
    open: false,
    environment: null
  });

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    handleClose();
  };

  const handleOpenCredentialsDialog = (environment) => {
    setCredentialsDialog({
      open: true,
      environment
    });
    handleClose();
  };

  const handleCloseCredentialsDialog = () => {
    setCredentialsDialog({
      open: false,
      environment: null
    });
  };

  return (
    <>
      <AppBar position="static" color="primary" enableColorOnDark>
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 2 }}
            onClick={toggleSidebar}
          >
            <MenuIcon />
          </IconButton>

          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            JBoss Monitor
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Production Credentials">
              <Button
                variant="outlined"
                color="inherit"
                size="small"
                startIcon={<KeyIcon />}
                onClick={() => handleOpenCredentialsDialog('production')}
              >
                Prod Creds
              </Button>
            </Tooltip>

            <Tooltip title="Non-Production Credentials">
              <Button
                variant="outlined"
                color="inherit"
                size="small"
                startIcon={<KeyIcon />}
                onClick={() => handleOpenCredentialsDialog('non_production')}
              >
                Non-Prod Creds
              </Button>
            </Tooltip>

            <Tooltip title="Refresh Data">
              <IconButton color="inherit">
                <RefreshIcon />
              </IconButton>
            </Tooltip>

            <Box>
              <Tooltip title="Account">
                <IconButton
                  size="large"
                  aria-label="account of current user"
                  aria-controls="menu-appbar"
                  aria-haspopup="true"
                  onClick={handleMenu}
                  color="inherit"
                >
                  <AccountCircle />
                </IconButton>
              </Tooltip>
              <Menu
                id="menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleClose}
              >
                <MenuItem disabled>
                  {currentUser?.username || 'User'}
                </MenuItem>
                <Divider />
                <MenuItem onClick={() => handleOpenCredentialsDialog('production')}>
                  Production Credentials
                </MenuItem>
                <MenuItem onClick={() => handleOpenCredentialsDialog('non_production')}>
                  Non-Production Credentials
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleLogout}>Logout</MenuItem>
              </Menu>
            </Box>
          </Box>
        </Toolbar>
      </AppBar>

      <JbossCredentialsDialog
        open={credentialsDialog.open}
        environment={credentialsDialog.environment}
        onClose={handleCloseCredentialsDialog}
      />
    </>
  );
};

export default Header;
