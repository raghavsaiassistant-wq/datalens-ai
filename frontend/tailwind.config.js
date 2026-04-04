module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#F5F5F7",
        card: "#FFFFFF",
        'space-gray': "#3A3A3C",
        secondary: "#6E6E73",
        tertiary: "#8E8E93",
        border: "rgba(0,0,0,0.08)",
        danger: "#FF3B30",
        warning: "#FF9500",
        success: "#34C759",
        accent: {
          DEFAULT: "#76B900",
          blue: "#0071E3"
        }
      },
      transitionDuration: {
        '400': '400ms',
        '1200': '1200ms',
      },
      transitionDelay: {
        '250': '250ms',
        '350': '350ms',
      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
      },
      fontFamily: {
        serif: ['"Instrument Serif"', 'serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
        sans: ['Archivo', 'sans-serif'],
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
