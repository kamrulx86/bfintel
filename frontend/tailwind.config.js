/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#06080C",
        surface: "#0C1018",
        surface2: "#121822",
        surface3: "#1A2230",
        text: "#EEF2F8",
        muted: "#8B96A8",
        primary: "#6B8CFF",
        "primary-dim": "#4A62C4",
        accent: "#22D3A8",
        success: "#34C759",
        warning: "#E5A020",
        critical: "#EF5F5F",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(107, 140, 255, 0.12)",
      },
    },
  },
  plugins: [],
};
