import { useNavigate } from "react-router";
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  TextField,
  Alert,
} from "@mui/material";
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  Delete as DeleteIcon,
  ShoppingCart as ShoppingCartIcon,
  ArrowBack as ArrowBackIcon,
  Login as LoginIcon,
} from "@mui/icons-material";
import { useOrders } from "../contexts/OrderContext";
import { useAuth } from "../contexts/AuthContext";

export default function Cart() {
  const navigate = useNavigate();
  const {
    cart,
    removeFromCart,
    updateCartItemQuantity,
    clearCart,
    getCartTotal,
  } = useOrders();
  const { isAuthenticated } = useAuth();

  const total = getCartTotal();
  const deliveryFee = 3.99;
  const serviceFee = total * 0.05;
  const grandTotal = total + deliveryFee + serviceFee;

  const handleCheckout = () => {
    if (isAuthenticated) {
      navigate("/create-order");
    } else {
      // Redirect to login with return URL
      navigate("/login", { state: { from: { pathname: "/create-order" } } });
    }
  };

  if (cart.items.length === 0) {
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
        <ShoppingCartIcon
          sx={{ fontSize: 80, color: "text.secondary", mb: 2 }}
        />
        <Typography variant="h5" fontWeight={600} gutterBottom>
          Ваш кошик порожній
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Додайте страви з ресторанів, щоб почати
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

  return (
    <Box>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 2,
          mb: 3,
        }}
      >
        <IconButton onClick={() => navigate(-1)}>
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h5" fontWeight={600}>
            Ваш кошик
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {cart.restaurantName}
          </Typography>
        </Box>
        <Button color="error" startIcon={<DeleteIcon />} onClick={clearCart}>
          Очистити
        </Button>
      </Box>

      {/* Login prompt for anonymous users */}
      {!isAuthenticated && (
        <Alert
          severity="info"
          sx={{ mb: 3, borderRadius: 2 }}
          action={
            <Button
              color="inherit"
              size="small"
              startIcon={<LoginIcon />}
              onClick={() =>
                navigate("/login", {
                  state: { from: { pathname: "/create-order" } },
                })
              }
            >
              Увійти
            </Button>
          }
        >
          Для оформлення замовлення необхідно увійти або зареєструватися. Ваш
          кошик буде збережено!
        </Alert>
      )}

      <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
        {/* Cart Items */}
        <Paper
          sx={{
            flex: 2,
            minWidth: 300,
            borderRadius: 3,
            boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
            p: 2,
          }}
        >
          <Typography variant="h6" fontWeight={600} sx={{ mb: 2, px: 1 }}>
            Товари ({cart.items.length})
          </Typography>
          <List>
            {cart.items.map((item, index) => (
              <Box key={item.menuItem.id}>
                <ListItem
                  sx={{ py: 2 }}
                  secondaryAction={
                    <IconButton
                      edge="end"
                      color="error"
                      onClick={() => removeFromCart(item.menuItem.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  }
                >
                  <ListItemAvatar>
                    <Avatar
                      src={item.menuItem.imageUrl}
                      alt={item.menuItem.name}
                      variant="rounded"
                      sx={{ width: 64, height: 64, mr: 1 }}
                    />
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Typography variant="subtitle1" fontWeight={600}>
                        {item.menuItem.name}
                      </Typography>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          ${item.menuItem.price.toFixed(2)} за шт.
                        </Typography>
                        {item.notes && (
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ fontStyle: "italic" }}
                          >
                            Примітка: {item.notes}
                          </Typography>
                        )}
                      </Box>
                    }
                    sx={{ mr: 2 }}
                  />
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mr: 4,
                    }}
                  >
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        border: "1px solid",
                        borderColor: "divider",
                        borderRadius: 2,
                      }}
                    >
                      <IconButton
                        size="small"
                        onClick={() =>
                          updateCartItemQuantity(
                            item.menuItem.id,
                            item.quantity - 1,
                          )
                        }
                      >
                        <RemoveIcon fontSize="small" />
                      </IconButton>
                      <Typography
                        sx={{ px: 2, minWidth: 30, textAlign: "center" }}
                      >
                        {item.quantity}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={() =>
                          updateCartItemQuantity(
                            item.menuItem.id,
                            item.quantity + 1,
                          )
                        }
                      >
                        <AddIcon fontSize="small" />
                      </IconButton>
                    </Box>
                    <Typography
                      variant="subtitle1"
                      fontWeight={700}
                      color="primary"
                      sx={{ minWidth: 70, textAlign: "right" }}
                    >
                      ${(item.menuItem.price * item.quantity).toFixed(2)}
                    </Typography>
                  </Box>
                </ListItem>
                {index < cart.items.length - 1 && <Divider />}
              </Box>
            ))}
          </List>
        </Paper>

        {/* Order Summary */}
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
            Підсумок замовлення
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
                Сума товарів
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
                Сервісний збір (5%)
              </Typography>
              <Typography variant="body2">${serviceFee.toFixed(2)}</Typography>
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              mb: 3,
            }}
          >
            <Typography variant="subtitle1" fontWeight={600}>
              Всього
            </Typography>
            <Typography variant="h5" fontWeight={700} color="primary">
              ${grandTotal.toFixed(2)}
            </Typography>
          </Box>

          <TextField
            fullWidth
            placeholder="Промокод"
            size="small"
            sx={{ mb: 2 }}
            slotProps={{
              input: {
                endAdornment: (
                  <Button size="small" sx={{ color: "#667eea" }}>
                    Застосувати
                  </Button>
                ),
              },
            }}
          />

          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={handleCheckout}
            startIcon={!isAuthenticated ? <LoginIcon /> : undefined}
            sx={{
              py: 1.5,
              fontSize: "1rem",
              fontWeight: 600,
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              "&:hover": {
                background: "linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%)",
              },
            }}
          >
            {isAuthenticated ? "Оформити замовлення" : "Увійти для оформлення"}
          </Button>

          <Button
            fullWidth
            variant="text"
            onClick={() => navigate(`/restaurants/${cart.restaurantId}`)}
            sx={{ mt: 1, color: "text.secondary" }}
          >
            Додати ще страви
          </Button>
        </Paper>
      </Box>
    </Box>
  );
}
