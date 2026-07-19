import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // "Switchboard" palette — inspired by mid-century telephone
        // dispatch consoles: graphite housings, amber signal lamps,
        // teal patch cables, cream paper tickets.
        graphite: {
          DEFAULT: "#20242A",
          50: "#F4F5F6",
          100: "#E2E5E8",
          200: "#C3C9D0",
          300: "#9AA3AD",
          400: "#6B7480",
          500: "#454C56",
          600: "#2E333B",
          700: "#20242A",
          800: "#16191E",
          900: "#0E1013",
        },
        amber: {
          DEFAULT: "#E8A33D",
          light: "#F4C878",
          dark: "#B87A22",
        },
        teal: {
          DEFAULT: "#3E7C7C",
          light: "#5FA3A3",
          dark: "#2A5959",
        },
        ticket: "#F1EADA",
        signal: {
          green: "#5FA36A",
          red: "#C4574A",
          amber: "#E8A33D",
        },
      },
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
      },
      backgroundImage: {
        "grain": "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.035) 1px, transparent 0)",
      },
      keyframes: {
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.25" },
        },
        rise: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        blink: "blink 1.6s ease-in-out infinite",
        rise: "rise 0.5s ease-out both",
      },
    },
  },
  plugins: [],
};
export default config;
