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
        gt: {
          purple: '#6d28d9',  // Primary brand color
          purple2: '#5b21b6', // Darker purple
          gray: '#f3f4f6',    // Light gray background
          darkgray: '#4b5563' // Dark gray for text
        }
      },
      // Definir tamaños de pantalla personalizados
      screens: {
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
        '3xl': '1920px', // Pantallas muy grandes
      },
      // Definir tamaño de contenedor para cada breakpoint
      container: {
        screens: {
          'sm': '100%',
          'md': '100%',
          'lg': '1024px',
          'xl': '1400px',
          '2xl': '1440px', // Aumentado para aprovechar más espacio
        },
      },
      boxShadow: {
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}