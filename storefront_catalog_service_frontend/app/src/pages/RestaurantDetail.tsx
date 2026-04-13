import { useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router";
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Typography,
  Chip,
  Button,
  IconButton,
  Tabs,
  Tab,
  Paper,
  Snackbar,
  Alert,
  Rating,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  ShoppingCart as ShoppingCartIcon,
  AccessTime as AccessTimeIcon,
  LocationOn as LocationOnIcon,
} from "@mui/icons-material";
import { getRestaurantById, getMenuByRestaurantId } from "../data/mockData";
import { useOrders } from "../contexts/OrderContext";
import type { MenuItem } from "../types";

export default function RestaurantDetail() {
  const { restaurantId } = useParams<{ restaurantId: string }>();
  const navigate = useNavigate();
  const { addToCart, cart, getCartItemCount } = useOrders();

  const restaurant = restaurantId ? getRestaurantById(restaurantId) : null;

  const menuItems = useMemo(
    () => (restaurantId ? getMenuByRestaurantId(restaurantId) : []),
    [restaurantId],
  );

  const categories = useMemo(() => {
    const cats = [...new Set(menuItems.map((item) => item.category))];
    return ["All", ...cats];
  }, [menuItems]);

  const [selectedCategory, setSelectedCategory] = useState("All");
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
  }>({ open: false, message: "" });

  const filteredItems =
    selectedCategory === "All"
      ? menuItems
      : menuItems.filter((item) => item.category === selectedCategory);

  const handleQuantityChange = (itemId: string, delta: number) => {
    setQuantities((prev) => {
      const current = prev[itemId] || 0;
      const newValue = Math.max(0, current + delta);
      return { ...prev, [itemId]: newValue };
    });
  };

  const handleAddToCart = (item: MenuItem) => {
    const quantity = quantities[item.id] || 1;
    addToCart(item, quantity);
    setQuantities((prev) => ({ ...prev, [item.id]: 0 }));
    setSnackbar({ open: true, message: `${item.name} added to cart!` });
  };

  if (!restaurant) {
    return (
      <Box sx={{ textAlign: "center", py: 8 }}>
        <Typography variant="h6">Restaurant not found</Typography>
        <Button onClick={() => navigate("/restaurants")} sx={{ mt: 2 }}>
          Back to Restaurants
        </Button>
      </Box>
    );
  }

  const cartItemCount = getCartItemCount();
  const isCartFromDifferentRestaurant =
    cart.restaurantId !== null && cart.restaurantId !== restaurantId;

  return (
    <Box>
      {/* Header */}
      <Paper
        sx={{
          borderRadius: 3,
          overflow: "hidden",
          mb: 3,
          boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
        }}
      >
        <Box sx={{ position: "relative" }}>
          <CardMedia
            component="img"
            height="200"
            image={restaurant.imageUrl}
            alt={restaurant.name}
            sx={{ objectFit: "cover" }}
          />
          <Box
            sx={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background:
                "linear-gradient(to bottom, transparent 50%, rgba(0,0,0,0.7) 100%)",
            }}
          />
          <IconButton
            onClick={() => navigate("/restaurants")}
            sx={{
              position: "absolute",
              top: 16,
              left: 16,
              backgroundColor: "white",
              "&:hover": { backgroundColor: "white" },
            }}
          >
            <ArrowBackIcon />
          </IconButton>
          {cartItemCount > 0 && (
            <Button
              variant="contained"
              startIcon={<ShoppingCartIcon />}
              onClick={() => navigate("/cart")}
              sx={{
                position: "absolute",
                top: 16,
                right: 16,
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              }}
            >
              Cart ({cartItemCount})
            </Button>
          )}
        </Box>
        <CardContent sx={{ pt: 3 }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              flexWrap: "wrap",
              gap: 2,
            }}
          >
            <Box>
              <Typography variant="h4" fontWeight={700}>
                {restaurant.name}
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
                {restaurant.description}
              </Typography>
            </Box>
            <Box sx={{ textAlign: "right" }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Rating value={restaurant.rating} precision={0.1} readOnly />
                <Typography variant="h6" fontWeight={600}>
                  {restaurant.rating}
                </Typography>
              </Box>
              <Chip
                label={restaurant.cuisine}
                color="primary"
                variant="outlined"
                sx={{ mt: 1 }}
              />
            </Box>
          </Box>
          <Box
            sx={{
              display: "flex",
              gap: 3,
              mt: 2,
              color: "text.secondary",
              flexWrap: "wrap",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <AccessTimeIcon fontSize="small" />
              <Typography variant="body2">{restaurant.deliveryTime}</Typography>
            </Box>
            <Typography variant="body2">
              Min. order: ${restaurant.minimumOrder}
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <LocationOnIcon fontSize="small" />
              <Typography variant="body2">{restaurant.address}</Typography>
            </Box>
          </Box>
        </CardContent>
      </Paper>

      {/* Warning if cart has items from different restaurant */}
      {isCartFromDifferentRestaurant && (
        <Alert severity="warning" sx={{ mb: 3, borderRadius: 2 }}>
          You have items from <strong>{cart.restaurantName}</strong> in your
          cart. Adding items from this restaurant will replace your current
          cart.
        </Alert>
      )}

      {/* Category Tabs */}
      <Paper
        sx={{
          mb: 3,
          borderRadius: 2,
          boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
        }}
      >
        <Tabs
          value={selectedCategory}
          onChange={(_, newValue) => setSelectedCategory(newValue)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            "& .MuiTab-root": {
              textTransform: "none",
              fontWeight: 500,
            },
          }}
        >
          {categories.map((category) => (
            <Tab key={category} label={category} value={category} />
          ))}
        </Tabs>
      </Paper>

      {/* Menu Items */}
      <Grid container spacing={3}>
        {filteredItems.map((item) => {
          const quantity = quantities[item.id] || 0;
          return (
            <Grid size={{ xs: 12, sm: 6, lg: 4 }} key={item.id}>
              <Card
                sx={{
                  borderRadius: 3,
                  boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                  opacity: item.isAvailable ? 1 : 0.6,
                  transition: "transform 0.2s",
                  "&:hover": {
                    transform: item.isAvailable ? "translateY(-4px)" : "none",
                  },
                }}
              >
                <CardMedia
                  component="img"
                  height="160"
                  image={item.imageUrl}
                  alt={item.name}
                  sx={{ objectFit: "cover" }}
                />
                <CardContent>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      mb: 1,
                    }}
                  >
                    <Typography variant="h6" fontWeight={600}>
                      {item.name}
                    </Typography>
                    <Typography variant="h6" fontWeight={700} color="primary">
                      ${item.price.toFixed(2)}
                    </Typography>
                  </Box>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 2, minHeight: 40 }}
                  >
                    {item.description}
                  </Typography>
                  {!item.isAvailable ? (
                    <Chip label="Not Available" color="default" size="small" />
                  ) : (
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 2,
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
                          onClick={() => handleQuantityChange(item.id, -1)}
                          disabled={quantity === 0}
                        >
                          <RemoveIcon fontSize="small" />
                        </IconButton>
                        <Typography
                          sx={{ px: 2, minWidth: 30, textAlign: "center" }}
                        >
                          {quantity || 1}
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={() => handleQuantityChange(item.id, 1)}
                        >
                          <AddIcon fontSize="small" />
                        </IconButton>
                      </Box>
                      <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => handleAddToCart(item)}
                        sx={{
                          flex: 1,
                          background:
                            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                          "&:hover": {
                            background:
                              "linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%)",
                          },
                        }}
                      >
                        Add
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={2000}
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
