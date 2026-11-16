export const colors = {
  // Backgrounds
  bg: "#0c0d11",          // page background — dark charcoal with blue tint
  surface: "#13141c",     // card background
  surfaceAlt: "#1a1b25",  // slightly elevated surface
  border: "#1e2030",      // subtle card border

  // Gradient accent (cyan → violet, like the slide)
  gradStart: "#06c8d4",
  gradMid: "#6366f1",
  gradEnd: "#8b2fc9",

  // Text
  white: "#ffffff",
  textMuted: "#8a8b9e",
  textDim: "#4a4b5e",

  // Status
  green: "#22c55e",
  red: "#ef4444",
  yellow: "#facc15",      // keep for booked status badge

  // Alias used in older code — maps to new palette
  black: "#0c0d11",
  card: "#13141c",
  zinc400: "#8a8b9e",
  zinc500: "#4a4b5e",
  zinc700: "#1e2030",
  zinc900: "#13141c",
};

export const font = {
  xs: 11,
  sm: 13,
  base: 15,
  lg: 18,
  xl: 22,
  "2xl": 28,
  "3xl": 34,
};

// Gradient presets
export const grad = {
  accent: ["#06c8d4", "#6366f1", "#8b2fc9"],    // cyan → indigo → violet
  accentH: ["#06c8d4", "#8b2fc9"],               // short two-stop
  subtle: ["#06c8d420", "#8b2fc920"],            // low-opacity tint for backgrounds
};
