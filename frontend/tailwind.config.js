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
        secondary: "#8E9AAF",
        danger: "#FF3B3B",
        warning: "#FFB800",
        success: "#00F08F",
        accent: {
          DEFAULT: "#76B900", // NVIDIA Green
          blue: "#00E5FF"    // Electric Cyan — matches CSS var --accent-blue
        }
      }
    },
  },
  plugins: [],
}
