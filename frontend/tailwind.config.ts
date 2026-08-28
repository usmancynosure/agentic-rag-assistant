import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F5F3FF",
        ink: "#1E1B4B",
        muted: "#5B5975",
        primary: {
          DEFAULT: "#6366F1",
          600: "#4F46E5",
          700: "#4338CA",
        },
        secondary: "#818CF8",
        accent: "#10B981",
      },
      fontFamily: {
        display: ['"Varela Round"', "system-ui", "sans-serif"],
        body: ['"Nunito Sans"', "system-ui", "sans-serif"],
      },
      borderRadius: {
        "2xl": "1.25rem",
        "3xl": "1.75rem",
        "4xl": "2.25rem",
      },
      boxShadow: {
        glass: "0 8px 30px rgba(79, 70, 229, 0.10)",
        soft: "0 4px 20px rgba(30, 27, 75, 0.06)",
        rail: "0 6px 24px rgba(79, 70, 229, 0.12)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.35s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
