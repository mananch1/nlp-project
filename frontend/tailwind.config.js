/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fssai: {
          blue: "#1a365d",
          orange: "#c53030",
          green: "#22543d"
        }
      }
    },
  },
  plugins: [],
}
