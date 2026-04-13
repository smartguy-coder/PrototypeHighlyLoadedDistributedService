import { useState } from "react";
import { useNavigate, Link as RouterLink } from "react-router";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  Link,
  InputAdornment,
  IconButton,
  ToggleButtonGroup,
  ToggleButton,
  CircularProgress,
  Grid,
} from "@mui/material";
import {
  Visibility,
  VisibilityOff,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Lock as LockIcon,
  Person as PersonIcon,
  ArrowBack as ArrowBackIcon,
} from "@mui/icons-material";
import { useAuth } from "../contexts/AuthContext";

type RegisterMethod = "email" | "phone" | "both";

export default function Register() {
  const navigate = useNavigate();
  const { register, error, clearError, isLoading } = useAuth();

  const [registerMethod, setRegisterMethod] = useState<RegisterMethod>("email");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleMethodChange = (
    _: React.MouseEvent<HTMLElement>,
    newMethod: RegisterMethod | null,
  ) => {
    if (newMethod) {
      setRegisterMethod(newMethod);
      clearError();
      setValidationError(null);
    }
  };

  const validateForm = (): boolean => {
    setValidationError(null);

    if (password.length < 8) {
      setValidationError("Пароль повинен містити мінімум 8 символів");
      return false;
    }

    if (password !== confirmPassword) {
      setValidationError("Паролі не співпадають");
      return false;
    }

    if (registerMethod === "email" && !email) {
      setValidationError("Введіть email");
      return false;
    }

    if (registerMethod === "phone" && !phone) {
      setValidationError("Введіть номер телефону");
      return false;
    }

    if (registerMethod === "both" && (!email || !phone)) {
      setValidationError("Введіть email та номер телефону");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validateForm()) {
      return;
    }

    try {
      await register({
        email: registerMethod !== "phone" ? email : undefined,
        phone: registerMethod !== "email" ? phone : undefined,
        password,
        first_name: firstName || undefined,
        last_name: lastName || undefined,
      });
      navigate("/", { replace: true });
    } catch {
      // Error handled in context
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
          maxWidth: 500,
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
            Створіть новий акаунт
          </Typography>
        </Box>

        {/* Register Method Toggle */}
        <ToggleButtonGroup
          value={registerMethod}
          exclusive
          onChange={handleMethodChange}
          fullWidth
          sx={{ mb: 3 }}
          size="small"
        >
          <ToggleButton value="email">
            <EmailIcon sx={{ mr: 0.5, fontSize: 18 }} />
            Email
          </ToggleButton>
          <ToggleButton value="phone">
            <PhoneIcon sx={{ mr: 0.5, fontSize: 18 }} />
            Телефон
          </ToggleButton>
          <ToggleButton value="both">Обидва</ToggleButton>
        </ToggleButtonGroup>

        {/* Error Alerts */}
        {(error || validationError) && (
          <Alert
            severity="error"
            sx={{ mb: 3, borderRadius: 2 }}
            onClose={() => {
              clearError();
              setValidationError(null);
            }}
          >
            {validationError || error}
          </Alert>
        )}

        {/* Register Form */}
        <Box component="form" onSubmit={handleSubmit}>
          {/* Name Fields */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="Ім'я"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonIcon color="action" />
                      </InputAdornment>
                    ),
                  },
                }}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="Прізвище"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
              />
            </Grid>
          </Grid>

          {/* Email Field */}
          {(registerMethod === "email" || registerMethod === "both") && (
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
          )}

          {/* Phone Field */}
          {(registerMethod === "phone" || registerMethod === "both") && (
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

          {/* Password Field */}
          <TextField
            fullWidth
            label="Пароль"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            helperText="Мінімум 8 символів"
            sx={{ mb: 2 }}
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

          {/* Confirm Password Field */}
          <TextField
            fullWidth
            label="Підтвердіть пароль"
            type={showPassword ? "text" : "password"}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            error={confirmPassword.length > 0 && password !== confirmPassword}
            helperText={
              confirmPassword.length > 0 && password !== confirmPassword
                ? "Паролі не співпадають"
                : ""
            }
            sx={{ mb: 3 }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon color="action" />
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
              "Зареєструватися"
            )}
          </Button>
        </Box>

        {/* Login Link */}
        <Box sx={{ textAlign: "center", mt: 3 }}>
          <Link
            component={RouterLink}
            to="/login"
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 0.5,
            }}
          >
            <ArrowBackIcon fontSize="small" />
            Вже маєте акаунт? Увійти
          </Link>
        </Box>
      </Paper>
    </Box>
  );
}
