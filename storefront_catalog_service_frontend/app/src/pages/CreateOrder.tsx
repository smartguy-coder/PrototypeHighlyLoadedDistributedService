import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Divider,
  List,
  ListItem,
  ListItemText,
  Alert,
  Snackbar,
  Stepper,
  Step,
  StepLabel,
  IconButton,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckCircleIcon,
} from "@mui/icons-material";
import { useOrders } from "../contexts/OrderContext";
import { useAuth } from "../contexts/AuthContext";

const steps = ["Перевірка замовлення", "Дані доставки", "Підтвердження"];

export default function CreateOrder() {
  const navigate = useNavigate();
  const { cart, getCartTotal, createOrder } = useOrders();
  const { user, isAuthenticated } = useAuth();

  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState(() => ({
    customerName: user
      ? `${user.first_name || ""} ${user.last_name || ""}`.trim()
      : "",
    customerPhone: user?.phone || "",
    deliveryAddress: "",
    notes: "",
  }));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [snackbar, setSnackbar] = useState({ open: false, message: "" });
  const [orderCreated, setOrderCreated] = useState(false);
  const [createdOrderId, setCreatedOrderId] = useState<string | null>(null);

  // Update form when user changes (only if fields are still empty)
  useEffect(() => {
    if (user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setFormData((prev) => {
        const updates: Partial<typeof prev> = {};
        if (!prev.customerName) {
          const name =
            `${user.first_name || ""} ${user.last_name || ""}`.trim();
          if (name) updates.customerName = name;
        }
        if (!prev.customerPhone && user.phone) {
          updates.customerPhone = user.phone;
        }
        return Object.keys(updates).length > 0 ? { ...prev, ...updates } : prev;
      });
    }
  }, [user]);

  const total = getCartTotal();
  const deliveryFee = 3.99;
  const serviceFee = total * 0.05;
  const grandTotal = total + deliveryFee + serviceFee;

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.customerName.trim()) {
      newErrors.customerName = "Ім'я обов'язкове";
    }
    if (!formData.customerPhone.trim()) {
      newErrors.customerPhone = "Телефон обов'язковий";
    } else if (!/^[\d\s\-+()]+$/.test(formData.customerPhone)) {
      newErrors.customerPhone = "Невірний формат телефону";
    }
    if (!formData.deliveryAddress.trim()) {
      newErrors.deliveryAddress = "Адреса доставки обов'язкова";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (activeStep === 1) {
      if (!validateForm()) return;
    }
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleSubmitOrder = () => {
    const order = createOrder(
      formData.customerName,
      formData.customerPhone,
      formData.deliveryAddress,
      formData.notes,
    );

    if (order) {
      setCreatedOrderId(order.id);
      setOrderCreated(true);
      setSnackbar({ open: true, message: "Замовлення успішно створено!" });
    } else {
      setSnackbar({ open: true, message: "Не вдалося створити замовлення" });
    }
  };

  // Redirect if not authenticated
  if (!isAuthenticated) {
    navigate("/login", { state: { from: { pathname: "/create-order" } } });
    return null;
  }

  if (cart.items.length === 0 && !orderCreated) {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "60vh",
          textAlign: "center",
        }}
      >
        <Typography variant="h5" fontWeight={600} gutterBottom>
          Кошик порожній
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Додайте товари в кошик перед оформленням
        </Typography>
        <Button
          variant="contained"
          onClick={() => navigate("/restaurants")}
          sx={{
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          }}
        >
          Переглянути ресторани
        </Button>
      </Box>
    );
  }

  if (orderCreated) {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "60vh",
          textAlign: "center",
        }}
      >
        <CheckCircleIcon sx={{ fontSize: 100, color: "success.main", mb: 3 }} />
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Замовлення створено!
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
          Номер замовлення: {createdOrderId}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Дякуємо за замовлення! Ви можете відстежувати його в розділі "Мої
          замовлення".
        </Typography>
        <Box sx={{ display: "flex", gap: 2 }}>
          <Button
            variant="contained"
            onClick={() => navigate("/orders")}
            sx={{
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            }}
          >
            Мої замовлення
          </Button>
          <Button variant="outlined" onClick={() => navigate("/restaurants")}>
            Замовити ще
          </Button>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate("/cart")}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5" fontWeight={600}>
          Оформлення замовлення
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

      <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
        {/* Main Content */}
        <Paper
          sx={{
            flex: 2,
            minWidth: 300,
            borderRadius: 3,
            boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
            p: 3,
          }}
        >
          {/* Step 0: Review Order */}
          {activeStep === 0 && (
            <>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
                Перевірте ваше замовлення
              </Typography>
              <Typography variant="subtitle2" color="text.secondary">
                {cart.restaurantName}
              </Typography>
              <List>
                {cart.items.map((item) => (
                  <ListItem key={item.menuItem.id} sx={{ px: 0 }}>
                    <ListItemText
                      primary={`${item.quantity}x ${item.menuItem.name}`}
                      secondary={item.notes}
                    />
                    <Typography variant="body1" fontWeight={600}>
                      ${(item.menuItem.price * item.quantity).toFixed(2)}
                    </Typography>
                  </ListItem>
                ))}
              </List>
              <Divider sx={{ my: 2 }} />
              <Alert severity="info" sx={{ borderRadius: 2 }}>
                Орієнтовний час доставки: 30-45 хвилин
              </Alert>
            </>
          )}

          {/* Step 1: Delivery Details */}
          {activeStep === 1 && (
            <>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 3 }}>
                Дані для доставки
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                <TextField
                  label="Повне ім'я"
                  fullWidth
                  value={formData.customerName}
                  onChange={(e) =>
                    handleInputChange("customerName", e.target.value)
                  }
                  error={!!errors.customerName}
                  helperText={errors.customerName}
                  required
                />
                <TextField
                  label="Номер телефону"
                  fullWidth
                  value={formData.customerPhone}
                  onChange={(e) =>
                    handleInputChange("customerPhone", e.target.value)
                  }
                  error={!!errors.customerPhone}
                  helperText={errors.customerPhone}
                  placeholder="+380 50 123 4567"
                  required
                />
                <TextField
                  label="Адреса доставки"
                  fullWidth
                  multiline
                  rows={2}
                  value={formData.deliveryAddress}
                  onChange={(e) =>
                    handleInputChange("deliveryAddress", e.target.value)
                  }
                  error={!!errors.deliveryAddress}
                  helperText={errors.deliveryAddress}
                  placeholder="Вулиця, будинок, квартира, місто"
                  required
                />
                <TextField
                  label="Коментар до замовлення (необов'язково)"
                  fullWidth
                  multiline
                  rows={2}
                  value={formData.notes}
                  onChange={(e) => handleInputChange("notes", e.target.value)}
                  placeholder="Напр., подзвоніть перед доставкою, код домофону тощо"
                />
              </Box>
            </>
          )}

          {/* Step 2: Confirmation */}
          {activeStep === 2 && (
            <>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 3 }}>
                Підтвердіть замовлення
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  gutterBottom
                >
                  Доставка на адресу
                </Typography>
                <Typography variant="body1" fontWeight={600}>
                  {formData.customerName}
                </Typography>
                <Typography variant="body2">
                  {formData.customerPhone}
                </Typography>
                <Typography variant="body2">
                  {formData.deliveryAddress}
                </Typography>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ mb: 3 }}>
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  gutterBottom
                >
                  Замовлення з {cart.restaurantName}
                </Typography>
                {cart.items.map((item) => (
                  <Box
                    key={item.menuItem.id}
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      py: 0.5,
                    }}
                  >
                    <Typography variant="body2">
                      {item.quantity}x {item.menuItem.name}
                    </Typography>
                    <Typography variant="body2">
                      ${(item.menuItem.price * item.quantity).toFixed(2)}
                    </Typography>
                  </Box>
                ))}
              </Box>

              {formData.notes && (
                <Box sx={{ mb: 2 }}>
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Коментар
                  </Typography>
                  <Typography variant="body2">{formData.notes}</Typography>
                </Box>
              )}

              <Alert severity="success" sx={{ borderRadius: 2 }}>
                Замовлення готове до оформлення!
              </Alert>
            </>
          )}

          {/* Navigation Buttons */}
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              mt: 4,
            }}
          >
            <Button
              disabled={activeStep === 0}
              onClick={handleBack}
              variant="outlined"
            >
              Назад
            </Button>
            {activeStep < steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={handleNext}
                sx={{
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                }}
              >
                Далі
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleSubmitOrder}
                sx={{
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  px: 4,
                }}
              >
                Підтвердити замовлення
              </Button>
            )}
          </Box>
        </Paper>

        {/* Order Summary Sidebar */}
        <Paper
          sx={{
            flex: 1,
            minWidth: 280,
            borderRadius: 3,
            boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
            p: 3,
            alignSelf: "flex-start",
          }}
        >
          <Typography variant="h6" fontWeight={600} sx={{ mb: 3 }}>
            Підсумок
          </Typography>

          <Box sx={{ mb: 2 }}>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                mb: 1.5,
              }}
            >
              <Typography variant="body2" color="text.secondary">
                Товари ({cart.items.length})
              </Typography>
              <Typography variant="body2">${total.toFixed(2)}</Typography>
            </Box>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                mb: 1.5,
              }}
            >
              <Typography variant="body2" color="text.secondary">
                Доставка
              </Typography>
              <Typography variant="body2">${deliveryFee.toFixed(2)}</Typography>
            </Box>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                mb: 1.5,
              }}
            >
              <Typography variant="body2" color="text.secondary">
                Сервісний збір
              </Typography>
              <Typography variant="body2">${serviceFee.toFixed(2)}</Typography>
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <Typography variant="subtitle1" fontWeight={600}>
              До сплати
            </Typography>
            <Typography variant="h5" fontWeight={700} color="primary">
              ${grandTotal.toFixed(2)}
            </Typography>
          </Box>
        </Paper>
      </Box>

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
