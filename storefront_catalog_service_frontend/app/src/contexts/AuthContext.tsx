import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { authService } from "../services/authService";
import type {
  User,
  LoginCredentials,
  RegisterData,
  OTPRequestData,
  OTPRequestResponse,
  OTPVerifyData,
} from "../types/auth";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Auth methods
  login: (credentials: LoginCredentials) => Promise<void>;
  loginWithOTP: (data: OTPVerifyData) => Promise<void>;
  requestOTP: (data: OTPRequestData) => Promise<OTPRequestResponse>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper to clear user cart on logout
function clearUserCart(userId: number): void {
  const key = `user_cart_${userId}`;
  localStorage.removeItem(key);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = !!user;

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      if (authService.isAuthenticated()) {
        try {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
        } catch {
          // Token might be invalid, clear it
          authService.clearTokens();
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  // Login with email/phone + password
  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.login(credentials);
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (err: unknown) {
      const errorMessage = extractErrorMessage(
        err,
        "Не вдалося увійти. Перевірте дані.",
      );
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Request OTP
  const requestOTP = useCallback(
    async (data: OTPRequestData): Promise<OTPRequestResponse> => {
      setError(null);

      try {
        const response = await authService.requestOTP(data);
        return response;
      } catch (err: unknown) {
        const errorMessage = extractErrorMessage(
          err,
          "Не вдалося надіслати код.",
        );
        setError(errorMessage);
        throw err;
      }
    },
    [],
  );

  // Login with OTP
  const loginWithOTP = useCallback(async (data: OTPVerifyData) => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.verifyOTP(data);
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (err: unknown) {
      const errorMessage = extractErrorMessage(
        err,
        "Невірний код підтвердження.",
      );
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Register
  const register = useCallback(async (data: RegisterData) => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.register(data);
      // Auto-login after registration
      await authService.login({
        email: data.email,
        phone: data.phone,
        password: data.password,
      });
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (err: unknown) {
      const errorMessage = extractErrorMessage(
        err,
        "Не вдалося зареєструватися.",
      );
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Logout - also clears user's cart
  const logout = useCallback(() => {
    // Clear user's cart before logging out
    if (user?.id) {
      clearUserCart(user.id);
    }
    authService.logout();
    setUser(null);
    setError(null);
  }, [user?.id]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    if (authService.isAuthenticated()) {
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        console.error("Failed to refresh user:", err);
      }
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        error,
        login,
        loginWithOTP,
        requestOTP,
        register,
        logout,
        clearError,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

// Helper to extract error messages from axios errors
function extractErrorMessage(err: unknown, defaultMessage: string): string {
  if (typeof err === "object" && err !== null) {
    const axiosError = err as { response?: { data?: Record<string, unknown> } };
    if (axiosError.response?.data) {
      const data = axiosError.response.data;
      // Handle various error formats
      if (typeof data === "string") return data;
      if (data.detail) return String(data.detail);
      if (data.message) return String(data.message);
      if (data.error) return String(data.error);
      // Handle field-specific errors
      const firstKey = Object.keys(data)[0];
      if (firstKey && Array.isArray(data[firstKey])) {
        return String(data[firstKey][0]);
      }
    }
  }
  return defaultMessage;
}
