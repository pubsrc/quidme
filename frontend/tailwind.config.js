/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          sky: "#0ea5e9",
          teal: "#14b8a6",
          mint: "#34d399",
          navy: "#0f172a"
        }
      }
    }
  },
  plugins: []
};
