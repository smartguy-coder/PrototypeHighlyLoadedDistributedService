import { useState } from "react";
import { useNavigate, useLocation, Link as RouterLink } from "react-router";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  Divider,
  Link,
  InputAdornment,
  IconButton,
  ToggleButtonGroup,
  ToggleButton,
  CircularProgress,
} from "@mui/material";
import {
  Visibility,
  VisibilityOff,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Lock as LockIcon,
} from "@mui/icons-material";
import { useAuth } from "../contexts/AuthContext";

type LoginMethod = "email" | "phone";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, error, clearError, isLoading } = useAuth();

  const [loginMethod, setLoginMethod] = useState<LoginMethod>("email");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname || "/";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    try {
      await login({
        email: loginMethod === "email" ? email : undefined,
        phone: loginMethod === "phone" ? phone : undefined,
        password,
      });
      navigate(from, { replace: true });
    } catch {
      // Error is handled in context
    }
  };

  const handleMethodChange = (
    _: React.MouseEvent<HTMLElement>,
    newMethod: LoginMethod | null,
  ) => {
    if (newMethod) {
      setLoginMethod(newMethod);
      clearError();
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#f5f7fa",
        p: 2,
      }}
    >
      <Paper
        sx={{
          maxWidth: 440,
          width: "100%",
          p: 4,
          borderRadius: 3,
          boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
        }}
      >
        {/* Header */}
        <Box sx={{ textAlign: "center", mb: 4 }}>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            🍽️ OrderHub
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Вхід до системи
          </Typography>
        </Box>

        {/* Login Method Toggle */}
        <ToggleButtonGroup
          value={loginMethod}
          exclusive
          onChange={handleMethodChange}
          fullWidth
          sx={{ mb: 3 }}
        >
          <ToggleButton value="email" sx={{ py: 1.5 }}>
            <EmailIcon sx={{ mr: 1 }} />
            Email
          </ToggleButton>
          <ToggleButton value="phone" sx={{ py: 1.5 }}>
            <PhoneIcon sx={{ mr: 1 }} />
            Телефон
          </ToggleButton>
        </ToggleButtonGroup>

        {/* Error Alert */}
        {error && (
          <Alert
            severity="error"
            sx={{ mb: 3, borderRadius: 2 }}
            onClose={clearError}
          >
            {error}
          </Alert>
        )}

        {/* Login Form */}
        <Box component="form" onSubmit={handleSubmit}>
          {loginMethod === "email" ? (
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              sx={{ mb: 2 }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <EmailIcon color="action" />
                    </InputAdornment>
                  ),
                },
              }}
            />
          ) : (
            <TextField
              fullWidth
              label="Телефон"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+380501234567"
              required
              sx={{ mb: 2 }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <PhoneIcon color="action" />
                    </InputAdornment>
                  ),
                },
              }}
            />
          )}

          <TextField
            fullWidth
            label="Пароль"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            sx={{ mb: 3 }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={isLoading}
            sx={{
              py: 1.5,
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              "&:hover": {
                background: "linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%)",
              },
            }}
          >
            {isLoading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              "Увійти"
            )}
          </Button>
        </Box>

        <Divider sx={{ my: 3 }}>
          <Typography variant="body2" color="text.secondary">
            або
          </Typography>
        </Divider>

        {/* OTP Login Link */}
        <Button
          fullWidth
          variant="outlined"
          size="large"
          component={RouterLink}
          to="/login/otp"
          sx={{ mb: 2 }}
        >
          Вхід за допомогою OTP коду
        </Button>

        {/* Register Link */}
        <Box sx={{ textAlign: "center", mt: 3 }}>
          <Typography variant="body2" color="text.secondary">
            Немає акаунту?{" "}
            <Link component={RouterLink} to="/register" fontWeight={600}>
              Зареєструватися
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
}
