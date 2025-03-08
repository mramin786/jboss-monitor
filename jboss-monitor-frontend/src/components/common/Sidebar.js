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
