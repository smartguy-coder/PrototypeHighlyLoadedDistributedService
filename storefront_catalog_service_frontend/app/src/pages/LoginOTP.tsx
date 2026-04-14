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
  ToggleButtonGroup,
  ToggleButton,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
} from "@mui/material";
import {
  Email as EmailIcon,
  Phone as PhoneIcon,
  ArrowBack as ArrowBackIcon,
} from "@mui/icons-material";
import { useAuth } from "../contexts/AuthContext";

type LoginMethod = "email" | "phone";

const steps = ["Введіть контакт", "Підтвердіть код"];

export default function LoginOTP() {
  const navigate = useNavigate();
  const { requestOTP, loginWithOTP, error, clearError, isLoading } = useAuth();

  const [activeStep, setActiveStep] = useState(0);
  const [loginMethod, setLoginMethod] = useState<LoginMethod>("email");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [secretCode, setSecretCode] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);

  const handleMethodChange = (
    _: React.MouseEvent<HTMLElement>,
    newMethod: LoginMethod | null,
  ) => {
    if (newMethod) {
      setLoginMethod(newMethod);
      clearError();
    }
  };

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    try {
      const response = await requestOTP({
        email: loginMethod === "email" ? email : undefined,
        phone: loginMethod === "phone" ? phone : undefined,
      });

      setVerificationCode(response.verification_code);
      setExpiresAt(response.expires_at);
      setOtpSent(true);
      setActiveStep(1);
    } catch {
      // Error handled in context
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    try {
      await loginWithOTP({
        email: loginMethod === "email" ? email : undefined,
        phone: loginMethod === "phone" ? phone : undefined,
        verification_code: verificationCode,
        secret_code: secretCode,
      });
      navigate("/", { replace: true });
    } catch {
      // Error handled in context
    }
  };

  const handleBack = () => {
    setActiveStep(0);
    setOtpSent(false);
    setSecretCode("");
    clearError();
  };

  const formatExpiry = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString("uk-UA", {
      hour: "2-digit",
      minute: "2-digit",
    });
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
        <Box sx={{ textAlign: "center", mb: 3 }}>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            🔐 OTP Вхід
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Вхід без пароля за допомогою одноразового коду
          </Typography>
        </Box>

        {/* Stepper */}
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

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

        {/* Step 1: Request OTP */}
        {!otpSent && (
          <Box component="form" onSubmit={handleRequestOTP}>
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

            {loginMethod === "email" ? (
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                sx={{ mb: 3 }}
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
                sx={{ mb: 3 }}
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
                  background:
                    "linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%)",
                },
              }}
            >
              {isLoading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                "Отримати код"
              )}
            </Button>
          </Box>
        )}

        {/* Step 2: Verify OTP */}
        {otpSent && (
          <Box component="form" onSubmit={handleVerifyOTP}>
            <Alert severity="info" sx={{ mb: 3, borderRadius: 2 }}>
              <Typography variant="body2">
                <strong>Код підтвердження:</strong> {verificationCode}
              </Typography>
              <Typography variant="body2">
                Секретний код надіслано на ваш{" "}
                {loginMethod === "email" ? "email" : "телефон"}.
              </Typography>
              {expiresAt && (
                <Typography variant="caption" color="text.secondary">
                  Дійсний до: {formatExpiry(expiresAt)}
                </Typography>
              )}
            </Alert>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Введіть 4-значний секретний код, який ви отримали:
            </Typography>

            <TextField
              fullWidth
              label="Секретний код"
              value={secretCode}
              onChange={(e) =>
                setSecretCode(e.target.value.replace(/\D/g, "").slice(0, 4))
              }
              placeholder="1234"
              required
              sx={{ mb: 3 }}
              slotProps={{
                input: {
                  sx: {
                    letterSpacing: "0.5em",
                    textAlign: "center",
                    fontSize: "1.5rem",
                  },
                  inputProps: {
                    maxLength: 4,
                    pattern: "[0-9]*",
                  },
                },
              }}
            />

            <Box sx={{ display: "flex", gap: 2 }}>
              <Button
                variant="outlined"
                size="large"
                onClick={handleBack}
                startIcon={<ArrowBackIcon />}
                sx={{ flex: 1 }}
              >
                Назад
              </Button>
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={isLoading || secretCode.length !== 4}
                sx={{
                  flex: 2,
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  "&:hover": {
                    background:
                      "linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%)",
                  },
                }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  "Підтвердити"
                )}
              </Button>
            </Box>
          </Box>
        )}

        {/* Back to Login Link */}
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
            Повернутися до входу з паролем
          </Link>
        </Box>
      </Paper>
    </Box>
  );
}
