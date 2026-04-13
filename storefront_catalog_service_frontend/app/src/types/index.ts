// Restaurant Types
export interface Restaurant {
  id: string;
  name: string;
  description: string;
  cuisine: string;
  address: string;
  rating: number;
  deliveryTime: string;
  minimumOrder: number;
  imageUrl: string;
  isOpen: boolean;
}

// Menu Types
export interface MenuItem {
  id: string;
  restaurantId: string;
  name: string;
  description: string;
  price: number;
  category: string;
  imageUrl: string;
  isAvailable: boolean;
}

// Order Types
export type OrderStatus =
  | "pending"
  | "confirmed"
  | "preparing"
  | "ready"
  | "delivering"
  | "delivered"
  | "cancelled";

export interface OrderItem {
  menuItem: MenuItem;
  quantity: number;
  notes?: string;
}

export interface Order {
  id: string;
  restaurantId: string;
  restaurantName: string;
  items: OrderItem[];
  status: OrderStatus;
  totalAmount: number;
  customerName: string;
  customerPhone: string;
  deliveryAddress: string;
  createdAt: Date;
  updatedAt: Date;
  notes?: string;
}

// Cart Types
export interface CartItem {
  menuItem: MenuItem;
  quantity: number;
  notes?: string;
}

export interface Cart {
  restaurantId: string | null;
  restaurantName: string | null;
  items: CartItem[];
}

// Re-export auth types
export * from "./auth";
