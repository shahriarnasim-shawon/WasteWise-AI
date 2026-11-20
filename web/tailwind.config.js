/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#fbfbfa",
        surface: "#ffffff",
        card: "#f4f4f2",
        border: "#e4e4e7",
        muted: "#71717a",
        primary: {
          DEFAULT: "#1e3a2b", // deep forest green
          hover: "#152a1f",
          light: "#eaf2ec"
        },
        terracotta: {
          DEFAULT: "#c25e3e",
          hover: "#a94e32",
          light: "#faede9"
        },
        accent: "#1e3a2b",
        success: "#1e3a2b",
        warning: "#d97706",
        danger: "#dc2626",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["SF Mono", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      borderRadius: {
        DEFAULT: "4px",
        sm: "3px",
        md: "6px",
        lg: "8px",
      }
    },
  },
  plugins: [],
}

