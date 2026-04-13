import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
  ReactNode,
} from "react";
import { ThemeProvider as MuiThemeProvider, PaletteMode } from "@mui/material";
import { createAppTheme, themeColors } from "../theme";

// Storage key for theme preference
const THEME_STORAGE_KEY = "orderhub-theme-mode";

// Get system preference
const getSystemPreference = (): PaletteMode => {
  if (typeof window !== "undefined" && window.matchMedia) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return "light";
};

// Get stored preference or system preference
const getInitialTheme = (): PaletteMode => {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === "light" || stored === "dark") {
      return stored;
    }
  }
  return getSystemPreference();
};

// Update document with theme class and CSS variables
const updateDocumentTheme = (themeMode: PaletteMode) => {
  const root = document.documentElement;

  // Set data attribute for CSS
  root.setAttribute("data-theme", themeMode);

  // Update CSS variables
  if (themeMode === "dark") {
    root.style.setProperty("--primary", "#8f9ff2");
    root.style.setProperty("--primary-light", "#b0bdff");
    root.style.setProperty("--primary-dark", "#667eea");
    root.style.setProperty("--secondary", "#b794d4");
    root.style.setProperty("--background", "#0f0f23");
    root.style.setProperty("--surface", "#1a1a2e");
    root.style.setProperty("--text-primary", "#f0f0f5");
    root.style.setProperty("--text-secondary", "#9ca3af");
    root.style.setProperty("--scrollbar-track", "#1a1a2e");
    root.style.setProperty("--scrollbar-thumb", "#3a3a4e");
    root.style.setProperty("--scrollbar-thumb-hover", "#4a4a5e");
  } else {
    root.style.setProperty("--primary", "#667eea");
    root.style.setProperty("--primary-light", "#8f9ff2");
    root.style.setProperty("--primary-dark", "#4a5db8");
    root.style.setProperty("--secondary", "#764ba2");
    root.style.setProperty("--background", "#f5f7fa");
    root.style.setProperty("--surface", "#ffffff");
    root.style.setProperty("--text-primary", "#1a1a2e");
    root.style.setProperty("--text-secondary", "#6b7280");
    root.style.setProperty("--scrollbar-track", "#f1f1f1");
    root.style.setProperty("--scrollbar-thumb", "#c1c1c1");
    root.style.setProperty("--scrollbar-thumb-hover", "#a1a1a1");
  }
};

interface ThemeContextType {
  mode: PaletteMode;
  toggleTheme: () => void;
  setMode: (mode: PaletteMode) => void;
  isDarkMode: boolean;
  colors: (typeof themeColors)["light"];
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [mode, setModeState] = useState<PaletteMode>(getInitialTheme);

  // Create MUI theme based on current mode
  const theme = useMemo(() => createAppTheme(mode), [mode]);

  // Get current theme colors
  const colors = useMemo(() => themeColors[mode], [mode]);

  // Set mode and persist to localStorage
  const setMode = useCallback((newMode: PaletteMode) => {
    setModeState(newMode);
    localStorage.setItem(THEME_STORAGE_KEY, newMode);
    updateDocumentTheme(newMode);
  }, []);

  // Toggle between light and dark
  const toggleTheme = useCallback(() => {
    setModeState((prevMode) => {
      const newMode = prevMode === "light" ? "dark" : "light";
      localStorage.setItem(THEME_STORAGE_KEY, newMode);
      updateDocumentTheme(newMode);
      return newMode;
    });
  }, []);

  // Initialize theme on mount
  useEffect(() => {
    updateDocumentTheme(mode);
  }, [mode]);

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent) => {
      // Only update if user hasn't manually set a preference
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      if (!stored) {
        setModeState(e.matches ? "dark" : "light");
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  const value = useMemo(
    () => ({
      mode,
      toggleTheme,
      setMode,
      isDarkMode: mode === "dark",
      colors,
    }),
    [mode, toggleTheme, setMode, colors],
  );

  return (
    <ThemeContext.Provider value={value}>
      <MuiThemeProvider theme={theme}>{children}</MuiThemeProvider>
    </ThemeContext.Provider>
  );
}

export function useThemeMode() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useThemeMode must be used within a ThemeProvider");
  }
  return context;
}
