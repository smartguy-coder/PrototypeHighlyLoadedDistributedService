import { useState } from "react";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Tabs,
  Tab,
  Divider,
  List,
  ListItem,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";
import {
  AccessTime as AccessTimeIcon,
  Person as PersonIcon,
  Phone as PhoneIcon,
  LocationOn as LocationOnIcon,
  Restaurant as RestaurantIcon,
} from "@mui/icons-material";
import { useOrders } from "../contexts/OrderContext";
import type { Order, OrderStatus } from "../types";

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
  ready: "Ready for Pickup",
  delivering: "Out for Delivery",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

const statusTabs: Array<{ value: OrderStatus | "all"; label: string }> = [
  { value: "all", label: "All Orders" },
  { value: "pending", label: "Pending" },
  { value: "confirmed", label: "Confirmed" },
  { value: "preparing", label: "Preparing" },
  { value: "ready", label: "Ready" },
  { value: "delivering", label: "Delivering" },
  { value: "delivered", label: "Delivered" },
  { value: "cancelled", label: "Cancelled" },
];

const nextStatusMap: Partial<Record<OrderStatus, OrderStatus>> = {
  pending: "confirmed",
  confirmed: "preparing",
  preparing: "ready",
  ready: "delivering",
  delivering: "delivered",
};

export default function Orders() {
  const { orders, updateOrderStatus } = useOrders();
  const [selectedTab, setSelectedTab] = useState<OrderStatus | "all">("all");
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const filteredOrders =
    selectedTab === "all"
      ? orders
      : orders.filter((o) => o.status === selectedTab);

  const handleStatusUpdate = (orderId: string, newStatus: OrderStatus) => {
    updateOrderStatus(orderId, newStatus);
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(date));
  };

  return (
    <Box>
      {/* Status Tabs */}
      <Tabs
        value={selectedTab}
        onChange={(_, newValue) => setSelectedTab(newValue)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{
          mb: 3,
          backgroundColor: "white",
          borderRadius: 2,
          boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
          "& .MuiTab-root": {
            textTransform: "none",
            fontWeight: 500,
            minHeight: 48,
          },
        }}
      >
        {statusTabs.map((tab) => {
          const count =
            tab.value === "all"
              ? orders.length
              : orders.filter((o) => o.status === tab.value).length;
          return (
            <Tab
              key={tab.value}
              label={`${tab.label} (${count})`}
              value={tab.value}
            />
          );
        })}
      </Tabs>

      {/* Orders Grid */}
      <Grid container spacing={3}>
        {filteredOrders.map((order) => (
          <Grid size={{ xs: 12, md: 6, lg: 4 }} key={order.id}>
            <Card
              sx={{
                borderRadius: 3,
                boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                transition: "transform 0.2s",
                "&:hover": { transform: "translateY(-4px)" },
              }}
            >
              <CardContent>
                {/* Header */}
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    mb: 2,
                  }}
                >
                  <Box>
                    <Typography variant="h6" fontWeight={600}>
                      {order.id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(order.createdAt)}
                    </Typography>
                  </Box>
                  <Chip
                    label={statusLabels[order.status]}
                    color={statusColors[order.status]}
                    size="small"
                    sx={{ fontWeight: 600 }}
                  />
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Restaurant */}
                <Box
                  sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}
                >
                  <RestaurantIcon color="action" fontSize="small" />
                  <Typography variant="subtitle2" fontWeight={600}>
                    {order.restaurantName}
                  </Typography>
                </Box>

                {/* Customer Info */}
                <Box sx={{ mb: 2 }}>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mb: 0.5,
                    }}
                  >
                    <PersonIcon color="action" fontSize="small" />
                    <Typography variant="body2">
                      {order.customerName}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mb: 0.5,
                    }}
                  >
                    <PhoneIcon color="action" fontSize="small" />
                    <Typography variant="body2">
                      {order.customerPhone}
                    </Typography>
                  </Box>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <LocationOnIcon color="action" fontSize="small" />
                    <Typography variant="body2" noWrap>
                      {order.deliveryAddress}
                    </Typography>
                  </Box>
                </Box>

                {/* Items Summary */}
                <Box
                  sx={{
                    backgroundColor: "rgba(0,0,0,0.02)",
                    borderRadius: 2,
                    p: 1.5,
                    mb: 2,
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    {order.items.length} item
                    {order.items.length > 1 ? "s" : ""}
                  </Typography>
                  <Typography variant="body2" noWrap>
                    {order.items.map((i) => i.menuItem.name).join(", ")}
                  </Typography>
                </Box>

                {/* Total */}
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    mb: 2,
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    Total
                  </Typography>
                  <Typography variant="h6" fontWeight={700} color="primary">
                    ${order.totalAmount.toFixed(2)}
                  </Typography>
                </Box>

                {/* Actions */}
                <Box sx={{ display: "flex", gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    fullWidth
                    onClick={() => {
                      setSelectedOrder(order);
                      setDialogOpen(true);
                    }}
                  >
                    View Details
                  </Button>
                  {nextStatusMap[order.status] && (
                    <Button
                      variant="contained"
                      size="small"
                      fullWidth
                      onClick={() =>
                        handleStatusUpdate(
                          order.id,
                          nextStatusMap[order.status]!,
                        )
                      }
                      sx={{
                        background:
                          "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                      }}
                    >
                      {order.status === "pending" && "Confirm"}
                      {order.status === "confirmed" && "Start Prep"}
                      {order.status === "preparing" && "Mark Ready"}
                      {order.status === "ready" && "Send Out"}
                      {order.status === "delivering" && "Delivered"}
                    </Button>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {filteredOrders.length === 0 && (
        <Box
          sx={{
            textAlign: "center",
            py: 8,
            color: "text.secondary",
          }}
        >
          <Typography variant="h6">No orders found</Typography>
          <Typography variant="body2">
            {selectedTab === "all"
              ? "No orders have been placed yet"
              : `No orders with status "${statusLabels[selectedTab as OrderStatus]}"`}
          </Typography>
        </Box>
      )}

      {/* Order Details Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        {selectedOrder && (
          <>
            <DialogTitle>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Typography variant="h6" fontWeight={600}>
                  Order {selectedOrder.id}
                </Typography>
                <Chip
                  label={statusLabels[selectedOrder.status]}
                  color={statusColors[selectedOrder.status]}
                  size="small"
                />
              </Box>
            </DialogTitle>
            <DialogContent>
              {/* Restaurant */}
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
              >
                Restaurant
              </Typography>
              <Typography variant="body1" fontWeight={600} sx={{ mb: 2 }}>
                {selectedOrder.restaurantName}
              </Typography>

              {/* Customer */}
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
              >
                Customer
              </Typography>
              <Typography variant="body2">
                {selectedOrder.customerName}
              </Typography>
              <Typography variant="body2">
                {selectedOrder.customerPhone}
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {selectedOrder.deliveryAddress}
              </Typography>

              {/* Items */}
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
              >
                Order Items
              </Typography>
              <List dense sx={{ mb: 2 }}>
                {selectedOrder.items.map((item, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemText
                      primary={`${item.quantity}x ${item.menuItem.name}`}
                      secondary={item.notes}
                    />
                    <Typography variant="body2" fontWeight={600}>
                      ${(item.menuItem.price * item.quantity).toFixed(2)}
                    </Typography>
                  </ListItem>
                ))}
              </List>

              <Divider sx={{ my: 2 }} />

              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Typography variant="subtitle1" fontWeight={600}>
                  Total
                </Typography>
                <Typography variant="h6" fontWeight={700} color="primary">
                  ${selectedOrder.totalAmount.toFixed(2)}
                </Typography>
              </Box>

              {selectedOrder.notes && (
                <Box sx={{ mt: 2 }}>
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Order Notes
                  </Typography>
                  <Typography variant="body2">{selectedOrder.notes}</Typography>
                </Box>
              )}

              {/* Status Update */}
              <Box sx={{ mt: 3 }}>
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  gutterBottom
                >
                  Update Status
                </Typography>
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={selectedOrder.status}
                    label="Status"
                    onChange={(e) => {
                      handleStatusUpdate(
                        selectedOrder.id,
                        e.target.value as OrderStatus,
                      );
                      setSelectedOrder({
                        ...selectedOrder,
                        status: e.target.value as OrderStatus,
                      });
                    }}
                  >
                    {Object.entries(statusLabels).map(([value, label]) => (
                      <MenuItem key={value} value={value}>
                        {label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>

              {/* Timestamps */}
              <Box
                sx={{
                  mt: 3,
                  display: "flex",
                  gap: 2,
                  color: "text.secondary",
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <AccessTimeIcon fontSize="small" />
                  <Typography variant="caption">
                    Created: {formatDate(selectedOrder.createdAt)}
                  </Typography>
                </Box>
                <Typography variant="caption">
                  Updated: {formatDate(selectedOrder.updatedAt)}
                </Typography>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDialogOpen(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
}
