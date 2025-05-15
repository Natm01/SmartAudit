/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        purple: {
          700: '#6d28d9',
          800: '#5b21b6',
        },
      },
    },
  },
  plugins: [],
}