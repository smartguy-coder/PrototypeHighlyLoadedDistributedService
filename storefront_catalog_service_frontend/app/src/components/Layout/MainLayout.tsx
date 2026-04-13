import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router";
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Badge,
  useTheme,
  useMediaQuery,
  CssBaseline,
  Avatar,
  Menu,
  MenuItem,
  Tooltip,
  Button,
} from "@mui/material";
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Restaurant as RestaurantIcon,
  ShoppingCart as ShoppingCartIcon,
  Receipt as ReceiptIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  Login as LoginIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
} from "@mui/icons-material";
import { useOrders } from "../../contexts/OrderContext";
import { useAuth } from "../../contexts/AuthContext";
import { useThemeMode } from "../../contexts/ThemeContext";

const drawerWidth = 280;

interface NavItem {
  text: string;
  icon: React.ReactNode;
  path: string;
  badge?: number;
  requiresAuth?: boolean;
}

export default function MainLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const { getCartItemCount, orders } = useOrders();
  const { user, isAuthenticated, logout } = useAuth();
  const { isDarkMode, toggleTheme, colors } = useThemeMode();

  const cartItemCount = getCartItemCount();
  const activeOrdersCount = orders.filter(
    (o) => !["delivered", "cancelled"].includes(o.status),
  ).length;

  // Define nav items - some require auth
  const allNavItems: NavItem[] = [
    { text: "Dashboard", icon: <DashboardIcon />, path: "/" },
    { text: "Ресторани", icon: <RestaurantIcon />, path: "/restaurants" },
    {
      text: "Мої замовлення",
      icon: <ReceiptIcon />,
      path: "/orders",
      badge: activeOrdersCount,
      requiresAuth: true,
    },
    {
      text: "Кошик",
      icon: <ShoppingCartIcon />,
      path: "/cart",
      badge: cartItemCount,
    },
  ];

  // Filter nav items based on auth state
  const navItems = allNavItems.filter(
    (item) => !item.requiresAuth || isAuthenticated,
  );

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleProfileMenuClose();
    logout();
    navigate("/");
  };

  const handleProfile = () => {
    handleProfileMenuClose();
    navigate("/profile");
  };

  const handleLogin = () => {
    navigate("/login");
  };

  const getUserInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    if (user?.email) {
      return user.email[0].toUpperCase();
    }
    if (user?.phone) {
      return "📱";
    }
    return "U";
  };

  const getUserDisplayName = () => {
    if (user?.first_name) {
      return `${user.first_name} ${user.last_name || ""}`.trim();
    }
    return user?.email || user?.phone || "User";
  };

  const drawerContent = (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Box
        sx={{
          p: 3,
          background: colors.gradient,
          color: "white",
        }}
      >
        <Typography variant="h5" fontWeight="bold">
          🍽️ OrderHub
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5 }}>
          Restaurant Order Integrator
        </Typography>
      </Box>

      <Divider />

      {/* User Info in Sidebar - only for authenticated users */}
      {isAuthenticated && user ? (
        <>
          <Box sx={{ p: 2, display: "flex", alignItems: "center", gap: 2 }}>
            <Avatar
              sx={{
                bgcolor: theme.palette.primary.main,
                width: 40,
                height: 40,
              }}
            >
              {getUserInitials()}
            </Avatar>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="subtitle2" fontWeight={600} noWrap>
                {getUserDisplayName()}
              </Typography>
              <Typography variant="caption" color="text.secondary" noWrap>
                {user.email || user.phone}
              </Typography>
            </Box>
          </Box>
          <Divider />
        </>
      ) : (
        <>
          <Box sx={{ p: 2 }}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<LoginIcon />}
              onClick={handleLogin}
              sx={{
                background: colors.gradient,
              }}
            >
              Увійти
            </Button>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "block", textAlign: "center", mt: 1 }}
            >
              Для оформлення замовлення
            </Typography>
          </Box>
          <Divider />
        </>
      )}

      <List sx={{ flex: 1, py: 2 }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.text} disablePadding sx={{ px: 1.5, py: 0.5 }}>
              <ListItemButton
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 2,
                  backgroundColor: isActive
                    ? colors.activeItemBg
                    : "transparent",
                  "&:hover": {
                    backgroundColor: isActive
                      ? colors.cardHoverBg
                      : theme.palette.action.hover,
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    color: isActive ? theme.palette.primary.main : "inherit",
                    minWidth: 44,
                  }}
                >
                  {item.badge !== undefined && item.badge > 0 ? (
                    <Badge badgeContent={item.badge} color="error">
                      {item.icon}
                    </Badge>
                  ) : (
                    item.icon
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  primaryTypographyProps={{
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? theme.palette.primary.main : "inherit",
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Divider />

      {/* Theme Toggle */}
      <List sx={{ py: 1 }}>
        <ListItem disablePadding sx={{ px: 1.5 }}>
          <ListItemButton
            onClick={toggleTheme}
            sx={{
              borderRadius: 2,
              "&:hover": {
                backgroundColor: theme.palette.action.hover,
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 44 }}>
              {isDarkMode ? (
                <LightModeIcon sx={{ color: "#fbbf24" }} />
              ) : (
                <DarkModeIcon sx={{ color: "#6366f1" }} />
              )}
            </ListItemIcon>
            <ListItemText
              primary={isDarkMode ? "Світла тема" : "Темна тема"}
              primaryTypographyProps={{
                fontWeight: 500,
              }}
            />
          </ListItemButton>
        </ListItem>
      </List>

      {/* Logout Button - only for authenticated users */}
      {isAuthenticated && (
        <>
          <Divider />
          <List sx={{ py: 1 }}>
            <ListItem disablePadding sx={{ px: 1.5 }}>
              <ListItemButton
                onClick={handleLogout}
                sx={{
                  borderRadius: 2,
                  "&:hover": {
                    backgroundColor: "rgba(244, 67, 54, 0.08)",
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 44, color: "error.main" }}>
                  <LogoutIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Вийти"
                  primaryTypographyProps={{
                    color: "error.main",
                    fontWeight: 500,
                  }}
                />
              </ListItemButton>
            </ListItem>
          </List>
        </>
      )}

      <Box sx={{ p: 2, textAlign: "center" }}>
        <Typography variant="caption" color="text.secondary">
          © 2026 OrderHub v1.0
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <CssBaseline />

      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          backgroundColor: colors.appBarBg,
          color: colors.appBarText,
          boxShadow: colors.shadow,
        }}
      >
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <IconButton
              color="inherit"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2, display: { md: "none" } }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div" fontWeight={600}>
              {navItems.find((item) => item.path === location.pathname)?.text ||
                "OrderHub"}
            </Typography>
          </Box>

          {/* Theme Toggle and User Menu */}
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {/* Theme Toggle in AppBar (visible on mobile) */}
            <Tooltip title={isDarkMode ? "Світла тема" : "Темна тема"}>
              <IconButton
                onClick={toggleTheme}
                color="inherit"
                sx={{ display: { xs: "flex", md: "none" } }}
              >
                {isDarkMode ? (
                  <LightModeIcon sx={{ color: "#fbbf24" }} />
                ) : (
                  <DarkModeIcon sx={{ color: "#6366f1" }} />
                )}
              </IconButton>
            </Tooltip>

            {isAuthenticated ? (
              <>
                <Tooltip title="Профіль">
                  <IconButton onClick={handleProfileMenuOpen} sx={{ p: 0.5 }}>
                    <Avatar
                      sx={{
                        bgcolor: theme.palette.primary.main,
                        width: 36,
                        height: 36,
                        fontSize: "0.9rem",
                      }}
                    >
                      {getUserInitials()}
                    </Avatar>
                  </IconButton>
                </Tooltip>
                <Menu
                  anchorEl={anchorEl}
                  open={Boolean(anchorEl)}
                  onClose={handleProfileMenuClose}
                  transformOrigin={{ horizontal: "right", vertical: "top" }}
                  anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
                  sx={{ mt: 1 }}
                >
                  <Box sx={{ px: 2, py: 1 }}>
                    <Typography variant="subtitle2" fontWeight={600}>
                      {getUserDisplayName()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {user?.email || user?.phone}
                    </Typography>
                  </Box>
                  <Divider />
                  <MenuItem onClick={handleProfile}>
                    <ListItemIcon>
                      <PersonIcon fontSize="small" />
                    </ListItemIcon>
                    Профіль
                  </MenuItem>
                  <MenuItem onClick={handleProfileMenuClose}>
                    <ListItemIcon>
                      <SettingsIcon fontSize="small" />
                    </ListItemIcon>
                    Налаштування
                  </MenuItem>
                  <Divider />
                  <MenuItem onClick={handleLogout} sx={{ color: "error.main" }}>
                    <ListItemIcon>
                      <LogoutIcon fontSize="small" color="error" />
                    </ListItemIcon>
                    Вийти
                  </MenuItem>
                </Menu>
              </>
            ) : (
              <Button
                variant="contained"
                startIcon={<LoginIcon />}
                onClick={handleLogin}
                size="small"
                sx={{
                  background: colors.gradient,
                }}
              >
                Увійти
              </Button>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      {/* Sidebar Drawer */}
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: "block", md: "none" },
            "& .MuiDrawer-paper": {
              boxSizing: "border-box",
              width: drawerWidth,
              backgroundColor: theme.palette.background.paper,
            },
          }}
        >
          {drawerContent}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: "none", md: "block" },
            "& .MuiDrawer-paper": {
              boxSizing: "border-box",
              width: drawerWidth,
              borderRight: `1px solid ${theme.palette.divider}`,
              backgroundColor: theme.palette.background.paper,
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          backgroundColor: theme.palette.background.default,
          minHeight: "100vh",
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
