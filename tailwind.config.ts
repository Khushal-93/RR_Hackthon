import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    screens: {
      sm: "360px",
      md: "768px",
      lg: "1024px",
      xl: "1200px",
      "2xl": "1440px",
    },
    extend: {
      maxWidth: {
        content: "1200px",
      },
      borderRadius: {
        card: "22px",
        pill: "980px",
      },
      boxShadow: {
        "apple-card": "var(--card-shadow)",
        "apple-hover": "var(--card-shadow-hover)",
        "apple-btn": "0 4px 14px rgba(43, 74, 203, 0.25)",
        "apple-pink-btn": "0 4px 18px rgba(255, 92, 147, 0.3)",
      },
      transitionTimingFunction: {
        apple: "cubic-bezier(0.25, 0.1, 0.25, 1)",
      },
      transitionDuration: {
        apple: "350ms",
      },
      colors: {
        primary: {
          DEFAULT: "var(--color-primary)",
          dark: "var(--color-primary-dark)",
        },
        secondary: {
          DEFAULT: "var(--color-secondary)",
          dark: "var(--color-secondary-dark)",
        },
        soft: {
          pink: "var(--color-soft-pink)",
          blue: "var(--color-soft-blue)",
        },
        canvas: {
          DEFAULT: "var(--color-bg-canvas)",
        },
        surface: {
          DEFAULT: "var(--color-bg-surface)",
          subtle: "var(--color-bg-subtle)",
          muted: "var(--color-bg-muted)",
        },
        border: {
          light: "var(--color-border-light)",
          medium: "var(--color-border-medium)",
          strong: "var(--color-border-strong)",
          focus: "var(--color-border-focus)",
        },
        text: {
          primary: "var(--color-text-primary)",
          secondary: "var(--color-text-secondary)",
          muted: "var(--color-text-muted)",
        },
        accent: {
          primary: "var(--color-accent-primary)",
          batter: "var(--color-accent-batter)",
          bowler: "var(--color-accent-bowler)",
          warning: "var(--color-accent-warning)",
          danger: "var(--color-accent-danger)",
          success: "var(--color-accent-success)",
        },
        tier: {
          elite: "var(--color-tier-elite)",
          above: "var(--color-tier-above)",
          average: "var(--color-tier-average)",
          below: "var(--color-tier-below)",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"SF Pro Display"',
          '"SF Pro Text"',
          '"Inter"',
          '"Helvetica Neue"',
          "Arial",
          "sans-serif",
        ],
        mono: [
          '"SF Mono"',
          "ui-monospace",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
