module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#0A0F1E",
        card: "rgba(255,255,255,0.05)",
        border: "rgba(255,255,255,0.1)",
        accent: {
          DEFAULT: "#76B900", // NVIDIA Green
          blue: "#3B82F6"
        }
      }
    },
  },
  plugins: [],
}
