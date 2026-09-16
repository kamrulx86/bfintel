/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0B0F14",
        surface: "#11161D",
        surface2: "#171D25",
        text: "#E6EAF0",
        muted: "#8993A3",
        primary: "#5B7CFA",
        "primary-dim": "#3D56C7",
        success: "#3D9A6A",
        warning: "#D4A017",
        critical: "#C44C4C",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
