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
      xl: "1440px",
    },
    extend: {
      spacing: {
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "8": "32px",
        "10": "40px",
        "12": "48px",
        "16": "64px",
      },
      colors: {
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
          neutral: "var(--color-accent-neutral)",
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
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
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
