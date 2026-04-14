import type { Restaurant, MenuItem, Order } from "../types";

export const mockRestaurants: Restaurant[] = [
  {
    id: "rest-001",
    name: "Bella Italia",
    description:
      "Authentic Italian cuisine with fresh pasta and wood-fired pizzas",
    cuisine: "Italian",
    address: "123 Main Street, Downtown",
    rating: 4.7,
    deliveryTime: "25-35 min",
    minimumOrder: 15,
    imageUrl: "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=400",
    isOpen: true,
  },
  {
    id: "rest-002",
    name: "Sakura Sushi",
    description: "Premium Japanese sushi and traditional dishes",
    cuisine: "Japanese",
    address: "456 Oak Avenue, Midtown",
    rating: 4.9,
    deliveryTime: "30-40 min",
    minimumOrder: 20,
    imageUrl:
      "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400",
    isOpen: true,
  },
  {
    id: "rest-003",
    name: "Spice Garden",
    description: "Flavorful Indian curries and tandoori specialties",
    cuisine: "Indian",
    address: "789 Curry Lane, East Side",
    rating: 4.5,
    deliveryTime: "35-45 min",
    minimumOrder: 18,
    imageUrl:
      "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400",
    isOpen: true,
  },
  {
    id: "rest-004",
    name: "The Burger Joint",
    description: "Gourmet burgers and craft beers",
    cuisine: "American",
    address: "321 Patty Road, West End",
    rating: 4.3,
    deliveryTime: "20-30 min",
    minimumOrder: 12,
    imageUrl:
      "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
    isOpen: false,
  },
  {
    id: "rest-005",
    name: "Taco Fiesta",
    description: "Authentic Mexican street food and margaritas",
    cuisine: "Mexican",
    address: "555 Salsa Street, South District",
    rating: 4.6,
    deliveryTime: "25-35 min",
    minimumOrder: 10,
    imageUrl:
      "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400",
    isOpen: true,
  },
  {
    id: "rest-006",
    name: "Golden Dragon",
    description: "Traditional Chinese cuisine with modern twist",
    cuisine: "Chinese",
    address: "888 Wok Way, Chinatown",
    rating: 4.4,
    deliveryTime: "30-40 min",
    minimumOrder: 15,
    imageUrl: "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400",
    isOpen: true,
  },
];

export const mockMenuItems: MenuItem[] = [
  // Bella Italia
  {
    id: "menu-001",
    restaurantId: "rest-001",
    name: "Margherita Pizza",
    description: "Classic tomato, mozzarella, and fresh basil",
    price: 14.99,
    category: "Pizza",
    imageUrl:
      "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=300",
    isAvailable: true,
  },
  {
    id: "menu-002",
    restaurantId: "rest-001",
    name: "Spaghetti Carbonara",
    description: "Creamy pasta with pancetta and parmesan",
    price: 16.99,
    category: "Pasta",
    imageUrl:
      "https://images.unsplash.com/photo-1612874742237-6526221588e3?w=300",
    isAvailable: true,
  },
  {
    id: "menu-003",
    restaurantId: "rest-001",
    name: "Tiramisu",
    description: "Classic Italian coffee-flavored dessert",
    price: 8.99,
    category: "Dessert",
    imageUrl:
      "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=300",
    isAvailable: true,
  },
  {
    id: "menu-004",
    restaurantId: "rest-001",
    name: "Bruschetta",
    description: "Toasted bread with tomato, basil, and olive oil",
    price: 9.99,
    category: "Appetizers",
    imageUrl:
      "https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?w=300",
    isAvailable: true,
  },

  // Sakura Sushi
  {
    id: "menu-005",
    restaurantId: "rest-002",
    name: "Dragon Roll",
    description: "Eel, avocado, cucumber with unagi sauce",
    price: 18.99,
    category: "Specialty Rolls",
    imageUrl:
      "https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?w=300",
    isAvailable: true,
  },
  {
    id: "menu-006",
    restaurantId: "rest-002",
    name: "Salmon Sashimi",
    description: "Fresh salmon slices (8 pcs)",
    price: 15.99,
    category: "Sashimi",
    imageUrl: "https://images.unsplash.com/photo-1534482421-64566f976cfa?w=300",
    isAvailable: true,
  },
  {
    id: "menu-007",
    restaurantId: "rest-002",
    name: "Miso Soup",
    description: "Traditional Japanese soup with tofu and seaweed",
    price: 4.99,
    category: "Soup",
    imageUrl:
      "https://images.unsplash.com/photo-1607330289024-1535c6b4e1c1?w=300",
    isAvailable: true,
  },
  {
    id: "menu-008",
    restaurantId: "rest-002",
    name: "Tempura Udon",
    description: "Thick noodles in broth with shrimp tempura",
    price: 16.99,
    category: "Noodles",
    imageUrl:
      "https://images.unsplash.com/photo-1618841557871-b4664fbf0cb3?w=300",
    isAvailable: true,
  },

  // Spice Garden
  {
    id: "menu-009",
    restaurantId: "rest-003",
    name: "Chicken Tikka Masala",
    description: "Creamy tomato curry with tender chicken",
    price: 17.99,
    category: "Curry",
    imageUrl:
      "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=300",
    isAvailable: true,
  },
  {
    id: "menu-010",
    restaurantId: "rest-003",
    name: "Garlic Naan",
    description: "Freshly baked bread with garlic butter",
    price: 4.99,
    category: "Bread",
    imageUrl:
      "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=300",
    isAvailable: true,
  },
  {
    id: "menu-011",
    restaurantId: "rest-003",
    name: "Vegetable Biryani",
    description: "Fragrant rice with mixed vegetables and spices",
    price: 14.99,
    category: "Rice",
    imageUrl:
      "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=300",
    isAvailable: true,
  },
  {
    id: "menu-012",
    restaurantId: "rest-003",
    name: "Samosa (2 pcs)",
    description: "Crispy pastry with spiced potato filling",
    price: 6.99,
    category: "Appetizers",
    imageUrl:
      "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=300",
    isAvailable: true,
  },

  // The Burger Joint
  {
    id: "menu-013",
    restaurantId: "rest-004",
    name: "Classic Cheeseburger",
    description: "Angus beef, cheddar, lettuce, tomato, pickles",
    price: 13.99,
    category: "Burgers",
    imageUrl:
      "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=300",
    isAvailable: true,
  },
  {
    id: "menu-014",
    restaurantId: "rest-004",
    name: "Loaded Fries",
    description: "Crispy fries with cheese, bacon, and sour cream",
    price: 8.99,
    category: "Sides",
    imageUrl:
      "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=300",
    isAvailable: true,
  },
  {
    id: "menu-015",
    restaurantId: "rest-004",
    name: "Onion Rings",
    description: "Beer-battered crispy onion rings",
    price: 6.99,
    category: "Sides",
    imageUrl:
      "https://images.unsplash.com/photo-1639024471283-03518883512d?w=300",
    isAvailable: true,
  },

  // Taco Fiesta
  {
    id: "menu-016",
    restaurantId: "rest-005",
    name: "Street Tacos (3 pcs)",
    description: "Corn tortillas with carne asada, onion, cilantro",
    price: 11.99,
    category: "Tacos",
    imageUrl: "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?w=300",
    isAvailable: true,
  },
  {
    id: "menu-017",
    restaurantId: "rest-005",
    name: "Burrito Supreme",
    description: "Large flour tortilla with rice, beans, meat, cheese",
    price: 14.99,
    category: "Burritos",
    imageUrl:
      "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=300",
    isAvailable: true,
  },
  {
    id: "menu-018",
    restaurantId: "rest-005",
    name: "Guacamole & Chips",
    description: "Fresh avocado dip with tortilla chips",
    price: 8.99,
    category: "Appetizers",
    imageUrl:
      "https://images.unsplash.com/photo-1615870216519-2f9fa575fa5c?w=300",
    isAvailable: true,
  },

  // Golden Dragon
  {
    id: "menu-019",
    restaurantId: "rest-006",
    name: "Kung Pao Chicken",
    description: "Spicy chicken with peanuts and vegetables",
    price: 15.99,
    category: "Main Dishes",
    imageUrl:
      "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=300",
    isAvailable: true,
  },
  {
    id: "menu-020",
    restaurantId: "rest-006",
    name: "Vegetable Spring Rolls",
    description: "Crispy rolls with mixed vegetables (4 pcs)",
    price: 7.99,
    category: "Appetizers",
    imageUrl: "https://images.unsplash.com/photo-1548507346-dad1bf31c3e7?w=300",
    isAvailable: true,
  },
  {
    id: "menu-021",
    restaurantId: "rest-006",
    name: "Fried Rice",
    description: "Wok-tossed rice with egg, vegetables, and soy sauce",
    price: 11.99,
    category: "Rice",
    imageUrl:
      "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=300",
    isAvailable: true,
  },
  {
    id: "menu-022",
    restaurantId: "rest-006",
    name: "Hot and Sour Soup",
    description: "Traditional spicy and tangy soup",
    price: 5.99,
    category: "Soup",
    imageUrl: "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=300",
    isAvailable: true,
  },
];

export const mockOrders: Order[] = [
  {
    id: "ord-001",
    restaurantId: "rest-001",
    restaurantName: "Bella Italia",
    items: [
      {
        menuItem: mockMenuItems[0],
        quantity: 2,
        notes: "Extra cheese please",
      },
      {
        menuItem: mockMenuItems[1],
        quantity: 1,
      },
    ],
    status: "delivered",
    totalAmount: 46.97,
    customerName: "John Smith",
    customerPhone: "+1 555-0101",
    deliveryAddress: "100 Customer Ave, Apt 4B",
    createdAt: new Date("2024-01-15T12:30:00"),
    updatedAt: new Date("2024-01-15T13:15:00"),
  },
  {
    id: "ord-002",
    restaurantId: "rest-002",
    restaurantName: "Sakura Sushi",
    items: [
      {
        menuItem: mockMenuItems[4],
        quantity: 1,
      },
      {
        menuItem: mockMenuItems[5],
        quantity: 2,
      },
      {
        menuItem: mockMenuItems[6],
        quantity: 2,
      },
    ],
    status: "preparing",
    totalAmount: 60.95,
    customerName: "Emily Johnson",
    customerPhone: "+1 555-0202",
    deliveryAddress: "250 Maple Street, Suite 12",
    createdAt: new Date("2024-01-15T18:45:00"),
    updatedAt: new Date("2024-01-15T19:00:00"),
    notes: "Please include extra soy sauce",
  },
  {
    id: "ord-003",
    restaurantId: "rest-003",
    restaurantName: "Spice Garden",
    items: [
      {
        menuItem: mockMenuItems[8],
        quantity: 2,
      },
      {
        menuItem: mockMenuItems[9],
        quantity: 3,
      },
      {
        menuItem: mockMenuItems[10],
        quantity: 1,
      },
    ],
    status: "confirmed",
    totalAmount: 65.94,
    customerName: "Michael Brown",
    customerPhone: "+1 555-0303",
    deliveryAddress: "789 Oak Boulevard",
    createdAt: new Date("2024-01-15T19:30:00"),
    updatedAt: new Date("2024-01-15T19:35:00"),
    notes: "Medium spice level please",
  },
  {
    id: "ord-004",
    restaurantId: "rest-005",
    restaurantName: "Taco Fiesta",
    items: [
      {
        menuItem: mockMenuItems[15],
        quantity: 2,
      },
      {
        menuItem: mockMenuItems[17],
        quantity: 1,
      },
    ],
    status: "pending",
    totalAmount: 32.97,
    customerName: "Sarah Davis",
    customerPhone: "+1 555-0404",
    deliveryAddress: "456 Pine Road",
    createdAt: new Date("2024-01-15T20:00:00"),
    updatedAt: new Date("2024-01-15T20:00:00"),
  },
  {
    id: "ord-005",
    restaurantId: "rest-006",
    restaurantName: "Golden Dragon",
    items: [
      {
        menuItem: mockMenuItems[18],
        quantity: 1,
      },
      {
        menuItem: mockMenuItems[19],
        quantity: 2,
      },
      {
        menuItem: mockMenuItems[20],
        quantity: 1,
      },
    ],
    status: "delivering",
    totalAmount: 43.96,
    customerName: "David Wilson",
    customerPhone: "+1 555-0505",
    deliveryAddress: "321 Cedar Lane, Unit 7",
    createdAt: new Date("2024-01-15T17:15:00"),
    updatedAt: new Date("2024-01-15T18:00:00"),
  },
  {
    id: "ord-006",
    restaurantId: "rest-001",
    restaurantName: "Bella Italia",
    items: [
      {
        menuItem: mockMenuItems[3],
        quantity: 1,
      },
      {
        menuItem: mockMenuItems[2],
        quantity: 2,
      },
    ],
    status: "cancelled",
    totalAmount: 27.97,
    customerName: "Lisa Anderson",
    customerPhone: "+1 555-0606",
    deliveryAddress: "555 Elm Street",
    createdAt: new Date("2024-01-14T14:00:00"),
    updatedAt: new Date("2024-01-14T14:30:00"),
    notes: "Customer requested cancellation",
  },
];

export const getMenuByRestaurantId = (restaurantId: string): MenuItem[] => {
  return mockMenuItems.filter((item) => item.restaurantId === restaurantId);
};

export const getRestaurantById = (
  restaurantId: string,
): Restaurant | undefined => {
  return mockRestaurants.find((r) => r.id === restaurantId);
};

export const getOrdersByStatus = (status: Order["status"] | "all"): Order[] => {
  if (status === "all") return mockOrders;
  return mockOrders.filter((order) => order.status === status);
};
