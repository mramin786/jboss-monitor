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

// src/components/common/Sidebar.js
import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Collapse,
  Box,
  Typography
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Storage as StorageIcon,
  ViewList as ViewListIcon,
  Description as DescriptionIcon,
  ExpandLess,
  ExpandMore,
  Computer as ComputerIcon,
  Speed as SpeedIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const drawerWidth = 240;

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const [open, setOpen] = useState(true);
  const [expandedMenus, setExpandedMenus] = useState({
    production: true,
    non_production: false
  });

  const handleToggleMenu = (menu) => {
    setExpandedMenus({
      ...expandedMenus,
      [menu]: !expandedMenus[menu]
    });
  };
  
  const isCurrentPath = (path) => {
    return location.pathname === path;
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        p: 2,
        backgroundColor: 'primary.dark'
      }}>
        <Typography variant="h6" color="white">
          JBoss Monitor
        </Typography>
      </Box>
      
      <Box sx={{ overflow: 'auto' }}>
        <List>
          <ListItem disablePadding>
            <ListItemButton 
              onClick={() => navigate('/')}
              selected={isCurrentPath('/')}
            >
              <ListItemIcon>
                <DashboardIcon color={isCurrentPath('/') ? 'primary' : 'inherit'} />
              </ListItemIcon>
              <ListItemText primary="Dashboard" />
            </ListItemButton>
          </ListItem>
          
          <Divider sx={{ my: 1 }} />
          
          {/* Production Environment */}
          <ListItem disablePadding>
            <ListItemButton onClick={() => handleToggleMenu('production')}>
              <ListItemIcon>
                <StorageIcon color="error" />
              </ListItemIcon>
              <ListItemText primary="Production" />
              {expandedMenus.production ? <ExpandLess /> : <ExpandMore />}
            </ListItemButton>
          </ListItem>
          
          <Collapse in={expandedMenus.production} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              <ListItemButton 
                sx={{ pl: 4 }}
                onClick={() => navigate('/production/hosts')}
                selected={isCurrentPath('/production/hosts')}
              >
                <ListItemIcon>
                  <ComputerIcon color={isCurrentPath('/production/hosts') ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="Hosts" />
              </ListItemButton>
              
              <ListItemButton 
                sx={{ pl: 4 }}
                onClick={() => navigate('/production/monitor')}
                selected={isCurrentPath('/production/monitor')}
              >
                <ListItemIcon>
                  <SpeedIcon color={isCurrentPath('/production/monitor') ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="Monitor" />
              </ListItemButton>
            </List>
          </Collapse>
          
          {/* Non-Production Environment */}
          <ListItem disablePadding>
            <ListItemButton onClick={() => handleToggleMenu('non_production')}>
              <ListItemIcon>
                <StorageIcon color="info" />
              </ListItemIcon>
              <ListItemText primary="Non-Production" />
              {expandedMenus.non_production ? <ExpandLess /> : <ExpandMore />}
            </ListItemButton>
          </ListItem>
          
          <Collapse in={expandedMenus.non_production} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              <ListItemButton 
                sx={{ pl: 4 }}
                onClick={() => navigate('/non_production/hosts')}
                selected={isCurrentPath('/non_production/hosts')}
              >
                <ListItemIcon>
                  <ComputerIcon color={isCurrentPath('/non_production/hosts') ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="Hosts" />
              </ListItemButton>
              
              <ListItemButton 
                sx={{ pl: 4 }}
                onClick={() => navigate('/non_production/monitor')}
                selected={isCurrentPath('/non_production/monitor')}
              >
                <ListItemIcon>
                  <SpeedIcon color={isCurrentPath('/non_production/monitor') ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="Monitor" />
              </ListItemButton>
            </List>
          </Collapse>
          
          <Divider sx={{ my: 1 }} />
          
          <ListItem disablePadding>
            <ListItemButton 
              onClick={() => navigate('/reports')}
              selected={isCurrentPath('/reports')}
            >
              <ListItemIcon>
                <DescriptionIcon color={isCurrentPath('/reports') ? 'primary' : 'inherit'} />
              </ListItemIcon>
              <ListItemText primary="Reports" />
            </ListItemButton>
          </ListItem>
        </List>
      </Box>
    </Drawer>
  );
};

export default Sidebar;

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
