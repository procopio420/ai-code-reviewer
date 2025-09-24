import type { Config } from "tailwindcss"
import plugin from "tailwindcss/plugin"

export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: { center: true, padding: "1rem", screens: { "2xl": "1100px" } },
    extend: {
      colors: {
        border: "hsl(215 20% 20%)",
        input: "hsl(215 20% 16%)",
        ring: "hsl(217 91% 60%)",
        background: "hsl(222 47% 8%)",
        foreground: "hsl(210 40% 98%)",
        primary: { DEFAULT: "hsl(217 91% 60%)", foreground: "white" },
        secondary: { DEFAULT: "hsl(224 14% 16%)", foreground: "hsl(210 40% 98%)" },
        card: { DEFAULT: "hsl(224 14% 12%)", foreground: "hsl(210 40% 98%)" },
        muted: { DEFAULT: "hsl(224 14% 18%)", foreground: "hsl(215 16% 72%)" },
        destructive: { DEFAULT: "hsl(0 72% 51%)", foreground: "white" },
      },
      borderRadius: { lg: "12px", md: "10px", sm: "8px" },
    },
  },
  plugins: [
    plugin(({ addBase }) => {
      addBase({
        "html, body, #root": { height: "100%" },
        "body": { background: "hsl(222 47% 8%)", color: "hsl(210 40% 98%)" },
      })
    })
  ],
} satisfies Config
