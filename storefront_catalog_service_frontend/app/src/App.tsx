import { Routes, Route, Navigate } from "react-router";
import CssBaseline from "@mui/material/CssBaseline";
import { OrderProvider } from "./contexts/OrderContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import MainLayout from "./components/Layout/MainLayout";
import ProtectedRoute from "./components/Auth/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import Restaurants from "./pages/Restaurants";
import RestaurantDetail from "./pages/RestaurantDetail";
import Orders from "./pages/Orders";
import Cart from "./pages/Cart";
import CreateOrder from "./pages/CreateOrder";
import Login from "./pages/Login";
import LoginOTP from "./pages/LoginOTP";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import { Box, CircularProgress, useTheme } from "@mui/material";

// Redirect authenticated users away from auth pages
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const theme = useTheme();

  if (isLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "100vh",
          backgroundColor: theme.palette.background.default,
        }}
      >
        <CircularProgress size={48} />
      </Box>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

// Loading component
function LoadingScreen() {
  const theme = useTheme();

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        backgroundColor: theme.palette.background.default,
      }}
    >
      <CircularProgress size={48} />
    </Box>
  );
}

// Main app wrapper - waits for auth to initialize
function AppContent() {
  const { isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Routes>
      {/* Auth routes - redirect if already logged in */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/login/otp"
        element={
          <PublicRoute>
            <LoginOTP />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />

      {/* Main layout - accessible to all (anonymous and logged in) */}
      <Route element={<MainLayout />}>
        {/* Public routes - accessible without login */}
        <Route path="/" element={<Dashboard />} />
        <Route path="/restaurants" element={<Restaurants />} />
        <Route
          path="/restaurants/:restaurantId"
          element={<RestaurantDetail />}
        />
        <Route path="/cart" element={<Cart />} />

        {/* Protected routes - require login */}
        <Route
          path="/orders"
          element={
            <ProtectedRoute>
              <Orders />
            </ProtectedRoute>
          }
        />
        <Route
          path="/create-order"
          element={
            <ProtectedRoute>
              <CreateOrder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Catch all - redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider>
      <CssBaseline />
      <AuthProvider>
        <OrderProvider>
          <AppContent />
        </OrderProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
