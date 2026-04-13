import axios, { type AxiosInstance, type AxiosError } from "axios";
import type {
  AuthTokens,
  LoginCredentials,
  RegisterData,
  OTPRequestData,
  OTPRequestResponse,
  OTPVerifyData,
  User,
  TokenRefreshResponse,
} from "../types/auth";

const API_BASE_URL = "http://localhost:8000/api/v1";

// Token storage keys
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

class AuthService {
  private api: AxiosInstance;
  private refreshPromise: Promise<string> | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor - add auth header
    this.api.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error),
    );

    // Response interceptor - handle token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config;

        // If 401 and we have a refresh token, try to refresh
        if (
          error.response?.status === 401 &&
          originalRequest &&
          !originalRequest.url?.includes("/auth/token/refresh/") &&
          !originalRequest.url?.includes("/auth/token/") &&
          this.getRefreshToken()
        ) {
          try {
            const newAccessToken = await this.refreshAccessToken();
            if (newAccessToken && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, clear tokens
            this.clearTokens();
            window.location.href = "/login";
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      },
    );
  }

  // Token management
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  setTokens(tokens: AuthTokens): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  }

  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  // Refresh access token
  async refreshAccessToken(): Promise<string | null> {
    // Prevent multiple simultaneous refresh calls
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    this.refreshPromise = (async () => {
      try {
        const response = await axios.post<TokenRefreshResponse>(
          `${API_BASE_URL}/auth/token/refresh/`,
          { refresh: refreshToken },
        );

        const newAccessToken = response.data.access;
        localStorage.setItem(ACCESS_TOKEN_KEY, newAccessToken);
        return newAccessToken;
      } catch (error) {
        this.clearTokens();
        throw error;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  // Login with password
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await this.api.post<AuthTokens>(
      "/auth/token/",
      credentials,
    );
    this.setTokens(response.data);
    return response.data;
  }

  // Register new user
  async register(data: RegisterData): Promise<User> {
    const response = await this.api.post<User>("/user/register/", data);
    return response.data;
  }

  // Logout
  logout(): void {
    this.clearTokens();
  }

  // Get current user profile
  async getCurrentUser(): Promise<User> {
    const response = await this.api.get<User>("/user/");
    return response.data;
  }

  // Update user profile
  async updateUser(data: Partial<User>): Promise<User> {
    const response = await this.api.patch<User>("/user/", data);
    return response.data;
  }

  // OTP Authentication
  async requestOTP(data: OTPRequestData): Promise<OTPRequestResponse> {
    const response = await this.api.post<OTPRequestResponse>(
      "/auth/otp/request/",
      data,
    );
    return response.data;
  }

  async verifyOTP(data: OTPVerifyData): Promise<AuthTokens> {
    const response = await this.api.post<AuthTokens>("/auth/otp/verify/", data);
    this.setTokens(response.data);
    return response.data;
  }

  // Verify token validity
  async verifyToken(token: string): Promise<boolean> {
    try {
      await this.api.post("/auth/token/verify/", { token });
      return true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;
