import { createTheme, ThemeOptions, PaletteMode } from "@mui/material/styles";

// Common theme options shared between light and dark modes
const getCommonOptions = (): ThemeOptions => ({
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 600,
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            borderRadius: 8,
          },
        },
      },
    },
  },
});

// Light theme palette
const lightPalette: ThemeOptions["palette"] = {
  mode: "light",
  primary: {
    main: "#667eea",
    light: "#8f9ff2",
    dark: "#4a5db8",
    contrastText: "#ffffff",
  },
  secondary: {
    main: "#764ba2",
    light: "#9470b8",
    dark: "#5a3780",
    contrastText: "#ffffff",
  },
  background: {
    default: "#f5f7fa",
    paper: "#ffffff",
  },
  text: {
    primary: "#1a1a2e",
    secondary: "#6b7280",
  },
  divider: "rgba(0, 0, 0, 0.08)",
  action: {
    hover: "rgba(0, 0, 0, 0.04)",
    selected: "rgba(102, 126, 234, 0.1)",
    selectedOpacity: 0.1,
  },
};

// Dark theme palette
const darkPalette: ThemeOptions["palette"] = {
  mode: "dark",
  primary: {
    main: "#8f9ff2",
    light: "#b0bdff",
    dark: "#667eea",
    contrastText: "#000000",
  },
  secondary: {
    main: "#b794d4",
    light: "#d4b8e8",
    dark: "#764ba2",
    contrastText: "#000000",
  },
  background: {
    default: "#0f0f23",
    paper: "#1a1a2e",
  },
  text: {
    primary: "#f0f0f5",
    secondary: "#9ca3af",
  },
  divider: "rgba(255, 255, 255, 0.08)",
  action: {
    hover: "rgba(255, 255, 255, 0.08)",
    selected: "rgba(143, 159, 242, 0.15)",
    selectedOpacity: 0.15,
  },
};

// Dark mode component overrides
const getDarkModeComponentOverrides = (): ThemeOptions["components"] => ({
  MuiAppBar: {
    styleOverrides: {
      root: {
        backgroundColor: "#1a1a2e",
        backgroundImage: "none",
      },
    },
  },
  MuiDrawer: {
    styleOverrides: {
      paper: {
        backgroundColor: "#1a1a2e",
        borderColor: "rgba(255, 255, 255, 0.08)",
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        backgroundImage: "none",
        backgroundColor: "#1a1a2e",
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        backgroundImage: "none",
      },
    },
  },
  MuiMenu: {
    styleOverrides: {
      paper: {
        backgroundColor: "#1a1a2e",
        backgroundImage: "none",
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        backgroundColor: "rgba(143, 159, 242, 0.15)",
      },
    },
  },
});

// Create theme based on mode
export const createAppTheme = (mode: PaletteMode) => {
  const commonOptions = getCommonOptions();
  const palette = mode === "light" ? lightPalette : darkPalette;

  let theme = createTheme({
    ...commonOptions,
    palette,
  });

  // Apply dark mode specific component overrides
  if (mode === "dark") {
    const darkOverrides = getDarkModeComponentOverrides();
    theme = createTheme(theme, {
      components: {
        ...theme.components,
        ...darkOverrides,
      },
    });
  }

  return theme;
};

// Export light and dark themes
export const lightTheme = createAppTheme("light");
export const darkTheme = createAppTheme("dark");

// Custom colors for consistent usage across components
export const themeColors = {
  light: {
    gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    appBarBg: "#ffffff",
    appBarText: "#1a1a2e",
    sidebarBg: "#ffffff",
    mainBg: "#f5f7fa",
    cardHoverBg: "rgba(102, 126, 234, 0.08)",
    activeItemBg: "rgba(102, 126, 234, 0.1)",
    shadow: "0 1px 3px rgba(0,0,0,0.1)",
    scrollbarTrack: "#f1f1f1",
    scrollbarThumb: "#c1c1c1",
    scrollbarThumbHover: "#a1a1a1",
  },
  dark: {
    gradient: "linear-gradient(135deg, #8f9ff2 0%, #b794d4 100%)",
    appBarBg: "#1a1a2e",
    appBarText: "#f0f0f5",
    sidebarBg: "#1a1a2e",
    mainBg: "#0f0f23",
    cardHoverBg: "rgba(143, 159, 242, 0.12)",
    activeItemBg: "rgba(143, 159, 242, 0.15)",
    shadow: "0 1px 3px rgba(0,0,0,0.3)",
    scrollbarTrack: "#1a1a2e",
    scrollbarThumb: "#3a3a4e",
    scrollbarThumbHover: "#4a4a5e",
  },
};
