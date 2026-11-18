/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f5ff',
          100: '#e0ecff',
          200: '#b9d5ff',
          300: '#7cb5ff',
          400: '#388eff',
          500: '#0c6bf2',
          600: '#0052cf',
          700: '#0040a8',
          800: '#043688',
          900: '#0a2f6e',
        }
      }
    },
  },
  plugins: [],
}
