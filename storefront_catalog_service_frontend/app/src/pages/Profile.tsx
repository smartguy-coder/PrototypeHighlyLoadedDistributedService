import { useState, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  Grid,
  Avatar,
  Chip,
  Divider,
  CircularProgress,
  Snackbar,
} from "@mui/material";
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Verified as VerifiedIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
} from "@mui/icons-material";
import { useAuth } from "../contexts/AuthContext";
import { authService } from "../services/authService";

export default function Profile() {
  const { user, refreshUser } = useAuth();

  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: "" });

  const [formData, setFormData] = useState({
    email: "",
    phone: "",
    first_name: "",
    last_name: "",
  });

  useEffect(() => {
    if (user) {
      setFormData({
        email: user.email || "",
        phone: user.phone || "",
        first_name: user.first_name || "",
        last_name: user.last_name || "",
      });
    }
  }, [user]);

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleEdit = () => {
    setIsEditing(true);
    setError(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
    if (user) {
      setFormData({
        email: user.email || "",
        phone: user.phone || "",
        first_name: user.first_name || "",
        last_name: user.last_name || "",
      });
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.updateUser({
        email: formData.email || null,
        phone: formData.phone || null,
        first_name: formData.first_name,
        last_name: formData.last_name,
      });

      await refreshUser();
      setIsEditing(false);
      setSnackbar({ open: true, message: "Профіль оновлено успішно!" });
    } catch (err: unknown) {
      const axiosError = err as {
        response?: { data?: Record<string, unknown> };
      };
      if (axiosError.response?.data) {
        const data = axiosError.response.data;
        const firstKey = Object.keys(data)[0];
        if (firstKey && Array.isArray(data[firstKey])) {
          setError(String(data[firstKey][0]));
        } else if (data.detail) {
          setError(String(data.detail));
        } else {
          setError("Помилка оновлення профілю");
        }
      } else {
        setError("Помилка оновлення профілю");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getUserInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    if (user?.email) {
      return user.email[0].toUpperCase();
    }
    return "U";
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("uk-UA", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (!user) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 800, mx: "auto" }}>
      {/* Header Card */}
      <Paper
        sx={{
          p: 4,
          mb: 3,
          borderRadius: 3,
          boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          color: "white",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 3 }}>
          <Avatar
            sx={{
              width: 80,
              height: 80,
              fontSize: "2rem",
              bgcolor: "rgba(255,255,255,0.2)",
              border: "3px solid rgba(255,255,255,0.5)",
            }}
          >
            {getUserInitials()}
          </Avatar>
          <Box>
            <Typography variant="h4" fontWeight={700}>
              {user.first_name || user.last_name
                ? `${user.first_name} ${user.last_name}`.trim()
                : "Користувач"}
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              {user.email || user.phone}
            </Typography>
            <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
              {user.is_email_verified && (
                <Chip
                  icon={<VerifiedIcon />}
                  label="Email підтверджено"
                  size="small"
                  sx={{
                    bgcolor: "rgba(255,255,255,0.2)",
                    color: "white",
                    "& .MuiChip-icon": { color: "white" },
                  }}
                />
              )}
              {user.is_phone_verified && (
                <Chip
                  icon={<VerifiedIcon />}
                  label="Телефон підтверджено"
                  size="small"
                  sx={{
                    bgcolor: "rgba(255,255,255,0.2)",
                    color: "white",
                    "& .MuiChip-icon": { color: "white" },
                  }}
                />
              )}
            </Box>
          </Box>
        </Box>
      </Paper>

      {/* Profile Form */}
      <Paper
        sx={{
          p: 4,
          borderRadius: 3,
          boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 3,
          }}
        >
          <Typography variant="h6" fontWeight={600}>
            Особисті дані
          </Typography>
          {!isEditing ? (
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={handleEdit}
            >
              Редагувати
            </Button>
          ) : (
            <Box sx={{ display: "flex", gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<CancelIcon />}
                onClick={handleCancel}
                color="inherit"
              >
                Скасувати
              </Button>
              <Button
                variant="contained"
                startIcon={
                  isLoading ? <CircularProgress size={20} /> : <SaveIcon />
                }
                onClick={handleSave}
                disabled={isLoading}
                sx={{
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                }}
              >
                Зберегти
              </Button>
            </Box>
          )}
        </Box>

        {error && (
          <Alert
            severity="error"
            sx={{ mb: 3, borderRadius: 2 }}
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Ім'я"
              value={formData.first_name}
              onChange={(e) => handleInputChange("first_name", e.target.value)}
              disabled={!isEditing}
              slotProps={{
                input: {
                  startAdornment: <PersonIcon color="action" sx={{ mr: 1 }} />,
                },
              }}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Прізвище"
              value={formData.last_name}
              onChange={(e) => handleInputChange("last_name", e.target.value)}
              disabled={!isEditing}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange("email", e.target.value)}
              disabled={!isEditing}
              helperText={
                isEditing && user.is_email_verified
                  ? "⚠️ Зміна email скине статус верифікації"
                  : ""
              }
              slotProps={{
                input: {
                  startAdornment: <EmailIcon color="action" sx={{ mr: 1 }} />,
                  endAdornment:
                    user.is_email_verified && !isEditing ? (
                      <VerifiedIcon color="success" />
                    ) : null,
                },
              }}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Телефон"
              type="tel"
              value={formData.phone}
              onChange={(e) => handleInputChange("phone", e.target.value)}
              disabled={!isEditing}
              placeholder="+380501234567"
              helperText={
                isEditing && user.is_phone_verified
                  ? "⚠️ Зміна телефону скине статус верифікації"
                  : ""
              }
              slotProps={{
                input: {
                  startAdornment: <PhoneIcon color="action" sx={{ mr: 1 }} />,
                  endAdornment:
                    user.is_phone_verified && !isEditing ? (
                      <VerifiedIcon color="success" />
                    ) : null,
                },
              }}
            />
          </Grid>
        </Grid>

        <Divider sx={{ my: 4 }} />

        {/* Account Info */}
        <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
          Інформація про акаунт
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="body2" color="text.secondary">
              ID користувача
            </Typography>
            <Typography variant="body1" fontWeight={500}>
              {user.id}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="body2" color="text.secondary">
              Статус
            </Typography>
            <Chip
              label={user.is_active ? "Активний" : "Неактивний"}
              color={user.is_active ? "success" : "default"}
              size="small"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="body2" color="text.secondary">
              Дата реєстрації
            </Typography>
            <Typography variant="body1" fontWeight={500}>
              {formatDate(user.date_joined)}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="body2" color="text.secondary">
              Останнє оновлення
            </Typography>
            <Typography variant="body1" fontWeight={500}>
              {formatDate(user.updated_at)}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity="success"
          sx={{ borderRadius: 2 }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
