/** @type {import('tailwindcss').Config} */
export default {
  // Theming is driven entirely by the CSS custom properties in
  // src/styles/tokens.css (swapped under [data-theme] / prefers-color-scheme),
  // not Tailwind's `dark:` variant, so no darkMode strategy is configured.
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "hsl(var(--color-bg) / <alpha-value>)",
        "bg-subtle": "hsl(var(--color-bg-subtle) / <alpha-value>)",
        fg: "hsl(var(--color-fg) / <alpha-value>)",
        "fg-muted": "hsl(var(--color-fg-muted) / <alpha-value>)",
        border: "hsl(var(--color-border) / <alpha-value>)",
        "border-strong": "hsl(var(--color-border-strong) / <alpha-value>)",
        primary: "hsl(var(--color-primary) / <alpha-value>)",
        "primary-foreground": "hsl(var(--color-primary-foreground) / <alpha-value>)",
        accent: "hsl(var(--color-accent) / <alpha-value>)",
        "accent-foreground": "hsl(var(--color-accent-foreground) / <alpha-value>)",
        success: "hsl(var(--color-success) / <alpha-value>)",
        warning: "hsl(var(--color-warning) / <alpha-value>)",
        danger: "hsl(var(--color-danger) / <alpha-value>)",
        "danger-foreground": "hsl(var(--color-danger-foreground) / <alpha-value>)",
        card: "hsl(var(--color-card) / <alpha-value>)",
        overlay: "hsl(var(--color-overlay) / <alpha-value>)",
      },
      fontFamily: {
        sans: "var(--font-sans)",
      },
      fontSize: {
        xs: "var(--text-xs)",
        sm: "var(--text-sm)",
        base: "var(--text-base)",
        lg: "var(--text-lg)",
        xl: "var(--text-xl)",
        "2xl": "var(--text-2xl)",
        "3xl": "var(--text-3xl)",
      },
      spacing: {
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        5: "var(--space-5)",
        6: "var(--space-6)",
        8: "var(--space-8)",
        10: "var(--space-10)",
        12: "var(--space-12)",
        sidebar: "var(--sidebar-width)",
        "sidebar-collapsed": "var(--sidebar-width-collapsed)",
        topbar: "var(--topbar-height)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        full: "var(--radius-full)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
      },
    },
  },
  plugins: [],
};
