import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import type { Cart, Order, MenuItem, OrderStatus } from "../types";
import {
  mockOrders as initialOrders,
  getRestaurantById,
} from "../data/mockData";
import { useAuth } from "./AuthContext";

// Storage keys
const ANONYMOUS_CART_KEY = "anonymous_cart";
const USER_CART_PREFIX = "user_cart_";
const CART_EXPIRY_DAYS = 2;

interface StoredCart {
  cart: Cart;
  expiresAt: number; // timestamp
}

interface OrderContextType {
  // Cart
  cart: Cart;
  addToCart: (item: MenuItem, quantity?: number, notes?: string) => void;
  removeFromCart: (menuItemId: string) => void;
  updateCartItemQuantity: (menuItemId: string, quantity: number) => void;
  clearCart: () => void;
  getCartTotal: () => number;
  getCartItemCount: () => number;

  // Orders
  orders: Order[];
  createOrder: (
    customerName: string,
    customerPhone: string,
    deliveryAddress: string,
    notes?: string,
  ) => Order | null;
  updateOrderStatus: (orderId: string, status: OrderStatus) => void;
  getOrderById: (orderId: string) => Order | undefined;
}

const OrderContext = createContext<OrderContextType | undefined>(undefined);

const initialCart: Cart = {
  restaurantId: null,
  restaurantName: null,
  items: [],
};

// Helper: Get storage key based on user
function getCartStorageKey(userId: number | null): string {
  return userId ? `${USER_CART_PREFIX}${userId}` : ANONYMOUS_CART_KEY;
}

// Helper: Save cart to localStorage
function saveCartToStorage(cart: Cart, userId: number | null): void {
  const key = getCartStorageKey(userId);
  const expiresAt = userId
    ? Date.now() + 365 * 24 * 60 * 60 * 1000 // 1 year for logged users (practically permanent)
    : Date.now() + CART_EXPIRY_DAYS * 24 * 60 * 60 * 1000; // 2 days for anonymous

  const storedCart: StoredCart = { cart, expiresAt };
  localStorage.setItem(key, JSON.stringify(storedCart));
}

// Helper: Load cart from localStorage
function loadCartFromStorage(userId: number | null): Cart | null {
  const key = getCartStorageKey(userId);
  const stored = localStorage.getItem(key);

  if (!stored) return null;

  try {
    const { cart, expiresAt }: StoredCart = JSON.parse(stored);

    // Check if expired
    if (Date.now() > expiresAt) {
      localStorage.removeItem(key);
      return null;
    }

    return cart;
  } catch {
    localStorage.removeItem(key);
    return null;
  }
}

// Helper: Clear cart from localStorage
function clearCartFromStorage(userId: number | null): void {
  const key = getCartStorageKey(userId);
  localStorage.removeItem(key);
}

// Helper: Get anonymous cart
function getAnonymousCart(): Cart | null {
  return loadCartFromStorage(null);
}

// Helper: Clear anonymous cart
function clearAnonymousCart(): void {
  clearCartFromStorage(null);
}

// Helper: Migrate anonymous cart to user
function migrateAnonymousCartToUser(userId: number): Cart | null {
  const anonymousCart = getAnonymousCart();
  if (anonymousCart && anonymousCart.items.length > 0) {
    // Save to user's cart
    saveCartToStorage(anonymousCart, userId);
    // Clear anonymous cart
    clearAnonymousCart();
    return anonymousCart;
  }
  return null;
}

export function OrderProvider({ children }: { children: ReactNode }) {
  const { user, isAuthenticated } = useAuth();
  const [cart, setCart] = useState<Cart>(initialCart);
  const [orders, setOrders] = useState<Order[]>(initialOrders);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize/restore cart when auth state changes
  useEffect(() => {
    const userId = user?.id ?? null;
    let newCart: Cart;

    if (isAuthenticated && userId) {
      // User just logged in - check for anonymous cart to migrate
      const migratedCart = migrateAnonymousCartToUser(userId);
      newCart = migratedCart || loadCartFromStorage(userId) || initialCart;
    } else {
      // Anonymous user - load anonymous cart
      newCart = loadCartFromStorage(null) || initialCart;
    }

    // Use functional update to avoid unnecessary re-renders
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCart((prevCart) => {
      // Only update if cart actually changed
      if (
        prevCart.restaurantId === newCart.restaurantId &&
        prevCart.items.length === newCart.items.length &&
        JSON.stringify(prevCart.items) === JSON.stringify(newCart.items)
      ) {
        return prevCart;
      }
      return newCart;
    });

    setIsInitialized(true);
  }, [isAuthenticated, user?.id]);

  // Save cart to storage whenever it changes (after initialization)
  useEffect(() => {
    if (isInitialized) {
      const userId = user?.id ?? null;
      saveCartToStorage(cart, userId);
    }
  }, [cart, user?.id, isInitialized]);

  const addToCart = useCallback(
    (item: MenuItem, quantity: number = 1, notes?: string) => {
      setCart((prevCart) => {
        // If cart is empty or from different restaurant, start fresh
        if (
          prevCart.restaurantId !== null &&
          prevCart.restaurantId !== item.restaurantId
        ) {
          const restaurant = getRestaurantById(item.restaurantId);
          return {
            restaurantId: item.restaurantId,
            restaurantName: restaurant?.name || null,
            items: [{ menuItem: item, quantity, notes }],
          };
        }

        // Check if item already exists in cart
        const existingItemIndex = prevCart.items.findIndex(
          (cartItem) => cartItem.menuItem.id === item.id,
        );

        if (existingItemIndex >= 0) {
          // Update quantity
          const updatedItems = [...prevCart.items];
          updatedItems[existingItemIndex] = {
            ...updatedItems[existingItemIndex],
            quantity: updatedItems[existingItemIndex].quantity + quantity,
            notes: notes || updatedItems[existingItemIndex].notes,
          };
          return { ...prevCart, items: updatedItems };
        }

        // Add new item
        const restaurant = getRestaurantById(item.restaurantId);
        return {
          restaurantId: item.restaurantId,
          restaurantName: restaurant?.name || prevCart.restaurantName,
          items: [...prevCart.items, { menuItem: item, quantity, notes }],
        };
      });
    },
    [],
  );

  const removeFromCart = useCallback((menuItemId: string) => {
    setCart((prevCart) => {
      const updatedItems = prevCart.items.filter(
        (item) => item.menuItem.id !== menuItemId,
      );
      if (updatedItems.length === 0) {
        return initialCart;
      }
      return { ...prevCart, items: updatedItems };
    });
  }, []);

  const updateCartItemQuantity = useCallback(
    (menuItemId: string, quantity: number) => {
      if (quantity <= 0) {
        removeFromCart(menuItemId);
        return;
      }
      setCart((prevCart) => ({
        ...prevCart,
        items: prevCart.items.map((item) =>
          item.menuItem.id === menuItemId ? { ...item, quantity } : item,
        ),
      }));
    },
    [removeFromCart],
  );

  const clearCart = useCallback(() => {
    const userId = user?.id ?? null;
    clearCartFromStorage(userId);
    setCart(initialCart);
  }, [user?.id]);

  const getCartTotal = useCallback(() => {
    return cart.items.reduce(
      (total, item) => total + item.menuItem.price * item.quantity,
      0,
    );
  }, [cart.items]);

  const getCartItemCount = useCallback(() => {
    return cart.items.reduce((count, item) => count + item.quantity, 0);
  }, [cart.items]);

  const createOrder = useCallback(
    (
      customerName: string,
      customerPhone: string,
      deliveryAddress: string,
      notes?: string,
    ): Order | null => {
      if (!cart.restaurantId || cart.items.length === 0) {
        return null;
      }

      const newOrder: Order = {
        id: `ord-${Date.now()}`,
        restaurantId: cart.restaurantId,
        restaurantName: cart.restaurantName || "Unknown Restaurant",
        items: cart.items.map((item) => ({
          menuItem: item.menuItem,
          quantity: item.quantity,
          notes: item.notes,
        })),
        status: "pending",
        totalAmount: getCartTotal(),
        customerName,
        customerPhone,
        deliveryAddress,
        createdAt: new Date(),
        updatedAt: new Date(),
        notes,
      };

      setOrders((prevOrders) => [newOrder, ...prevOrders]);
      clearCart();
      return newOrder;
    },
    [cart, getCartTotal, clearCart],
  );

  const updateOrderStatus = useCallback(
    (orderId: string, status: OrderStatus) => {
      setOrders((prevOrders) =>
        prevOrders.map((order) =>
          order.id === orderId
            ? { ...order, status, updatedAt: new Date() }
            : order,
        ),
      );
    },
    [],
  );

  const getOrderById = useCallback(
    (orderId: string) => {
      return orders.find((order) => order.id === orderId);
    },
    [orders],
  );

  return (
    <OrderContext.Provider
      value={{
        cart,
        addToCart,
        removeFromCart,
        updateCartItemQuantity,
        clearCart,
        getCartTotal,
        getCartItemCount,
        orders,
        createOrder,
        updateOrderStatus,
        getOrderById,
      }}
    >
      {children}
    </OrderContext.Provider>
  );
}

export function useOrders() {
  const context = useContext(OrderContext);
  if (context === undefined) {
    throw new Error("useOrders must be used within an OrderProvider");
  }
  return context;
}

// Export helper for clearing cart on logout
export function clearUserCartOnLogout(userId: number): void {
  clearCartFromStorage(userId);
}
