module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#0A0C10",
        card: "rgba(255,255,255,0.03)",
        border: "rgba(255,255,255,0.08)",
        secondary: "#8E9AAF",
        danger: "#FF3B3B",
        warning: "#FFB800",
        success: "#00F08F",
        accent: {
          DEFAULT: "#76B900",
          blue: "#00E5FF"
        }
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
