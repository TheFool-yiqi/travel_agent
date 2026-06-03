import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "var(--color-primary)",
        "primary-light": "var(--color-primary-light)",
        accent: "var(--color-accent)",
        "sand-bg": "var(--color-sand-bg)",
        "sand-surface": "var(--color-sand-surface)",
        ink: "var(--color-ink)",
        "ink-muted": "var(--color-ink-muted)",
        border: "var(--color-border)",
        "text-serif": "var(--text-serif)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        serif: ["var(--font-serif)", "serif"],
        display: ["var(--font-display)", "serif"],
      },
      borderRadius: {
        lg: "var(--radius-lg)",
        md: "var(--radius-md)",
        sm: "var(--radius-sm)",
      },
    },
  },
  plugins: [],
} satisfies Config;
