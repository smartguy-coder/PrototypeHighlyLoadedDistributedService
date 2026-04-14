import { useNavigate } from "react-router";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
  Button,
} from "@mui/material";
import {
  TrendingUp as TrendingUpIcon,
  Restaurant as RestaurantIcon,
  ShoppingCart as ShoppingCartIcon,
  CheckCircle as CheckCircleIcon,
  AccessTime as AccessTimeIcon,
  LocalShipping as LocalShippingIcon,
} from "@mui/icons-material";
import { useOrders } from "../contexts/OrderContext";
import { mockRestaurants } from "../data/mockData";
import type { OrderStatus } from "../types";

const statusColors: Record<
  OrderStatus,
  "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning"
> = {
  pending: "warning",
  confirmed: "info",
  preparing: "primary",
  ready: "secondary",
  delivering: "info",
  delivered: "success",
  cancelled: "error",
};

const statusLabels: Record<OrderStatus, string> = {
  pending: "Pending",
  confirmed: "Confirmed",
  preparing: "Preparing",
  ready: "Ready",
  delivering: "Delivering",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { orders } = useOrders();

  const activeOrders = orders.filter(
    (o) => !["delivered", "cancelled"].includes(o.status),
  );
  const todayOrders = orders.filter(
    (o) => new Date(o.createdAt).toDateString() === new Date().toDateString(),
  );
  const todayRevenue = todayOrders.reduce((sum, o) => sum + o.totalAmount, 0);
  const openRestaurants = mockRestaurants.filter((r) => r.isOpen).length;

  const stats = [
    {
      title: "Active Orders",
      value: activeOrders.length,
      icon: <ShoppingCartIcon />,
      color: "#667eea",
      bgColor: "rgba(102, 126, 234, 0.1)",
    },
    {
      title: "Today's Orders",
      value: todayOrders.length,
      icon: <TrendingUpIcon />,
      color: "#f5576c",
      bgColor: "rgba(245, 87, 108, 0.1)",
    },
    {
      title: "Today's Revenue",
      value: `$${todayRevenue.toFixed(2)}`,
      icon: <CheckCircleIcon />,
      color: "#4facfe",
      bgColor: "rgba(79, 172, 254, 0.1)",
    },
    {
      title: "Open Restaurants",
      value: `${openRestaurants}/${mockRestaurants.length}`,
      icon: <RestaurantIcon />,
      color: "#00f2fe",
      bgColor: "rgba(0, 242, 254, 0.1)",
    },
  ];

  return (
    <Box>
      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={stat.title}>
            <Card
              sx={{
                borderRadius: 3,
                boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                transition: "transform 0.2s",
                "&:hover": { transform: "translateY(-4px)" },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      backgroundColor: stat.bgColor,
                      color: stat.color,
                      mr: 2,
                    }}
                  >
                    {stat.icon}
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {stat.title}
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">
                  {stat.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Recent Orders */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 3,
              boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
            }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                mb: 2,
              }}
            >
              <Typography variant="h6" fontWeight={600}>
                Recent Orders
              </Typography>
              <Button
                size="small"
                onClick={() => navigate("/orders")}
                sx={{ color: "#667eea" }}
              >
                View All
              </Button>
            </Box>
            <List sx={{ p: 0 }}>
              {orders.slice(0, 5).map((order, index) => (
                <ListItem
                  key={order.id}
                  sx={{
                    px: 0,
                    py: 2,
                    borderBottom:
                      index < 4 ? "1px solid rgba(0,0,0,0.06)" : "none",
                  }}
                >
                  <ListItemAvatar>
                    <Avatar
                      sx={{
                        backgroundColor: "rgba(102, 126, 234, 0.1)",
                        color: "#667eea",
                      }}
                    >
                      {order.status === "delivering" ? (
                        <LocalShippingIcon />
                      ) : (
                        <AccessTimeIcon />
                      )}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 1,
                        }}
                      >
                        <Typography variant="subtitle2" fontWeight={600}>
                          {order.id}
                        </Typography>
                        <Chip
                          size="small"
                          label={statusLabels[order.status]}
                          color={statusColors[order.status]}
                          sx={{ height: 22, fontSize: "0.7rem" }}
                        />
                      </Box>
                    }
                    secondary={`${order.restaurantName} • ${order.customerName}`}
                  />
                  <Typography variant="subtitle2" fontWeight={600}>
                    ${order.totalAmount.toFixed(2)}
                  </Typography>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Popular Restaurants */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 3,
              boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
            }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                mb: 2,
              }}
            >
              <Typography variant="h6" fontWeight={600}>
                Top Restaurants
              </Typography>
              <Button
                size="small"
                onClick={() => navigate("/restaurants")}
                sx={{ color: "#667eea" }}
              >
                View All
              </Button>
            </Box>
            <List sx={{ p: 0 }}>
              {mockRestaurants
                .sort((a, b) => b.rating - a.rating)
                .slice(0, 4)
                .map((restaurant, index) => (
                  <ListItem
                    key={restaurant.id}
                    sx={{
                      px: 0,
                      py: 2,
                      borderBottom:
                        index < 3 ? "1px solid rgba(0,0,0,0.06)" : "none",
                    }}
                  >
                    <ListItemAvatar>
                      <Avatar
                        src={restaurant.imageUrl}
                        alt={restaurant.name}
                        sx={{ width: 48, height: 48, borderRadius: 2 }}
                        variant="rounded"
                      />
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Typography variant="subtitle2" fontWeight={600}>
                          {restaurant.name}
                        </Typography>
                      }
                      secondary={restaurant.cuisine}
                      sx={{ ml: 1 }}
                    />
                    <Box sx={{ textAlign: "right" }}>
                      <Typography
                        variant="subtitle2"
                        fontWeight={600}
                        color="warning.main"
                      >
                        ⭐ {restaurant.rating}
                      </Typography>
                      <Chip
                        size="small"
                        label={restaurant.isOpen ? "Open" : "Closed"}
                        color={restaurant.isOpen ? "success" : "default"}
                        sx={{ height: 20, fontSize: "0.65rem", mt: 0.5 }}
                      />
                    </Box>
                  </ListItem>
                ))}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
