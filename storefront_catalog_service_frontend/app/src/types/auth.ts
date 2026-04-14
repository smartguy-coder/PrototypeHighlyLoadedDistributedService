// User types
export interface User {
  id: number;
  email: string | null;
  phone: string | null;
  first_name: string;
  last_name: string;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  is_active: boolean;
  date_joined: string;
  created_at: string;
  updated_at: string;
}

// Auth tokens
export interface AuthTokens {
  access: string;
  refresh: string;
}

// Login with password
export interface LoginCredentials {
  email?: string;
  phone?: string;
  password: string;
}

// Registration
export interface RegisterData {
  email?: string;
  phone?: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

// OTP Request
export interface OTPRequestData {
  email?: string;
  phone?: string;
}

export interface OTPRequestResponse {
  verification_code: string;
  expires_at: string;
}

// OTP Verify
export interface OTPVerifyData {
  email?: string;
  phone?: string;
  verification_code: string;
  secret_code: string;
}

// Auth state
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Token refresh
export interface TokenRefreshRequest {
  refresh: string;
}

export interface TokenRefreshResponse {
  access: string;
}
