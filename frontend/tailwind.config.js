/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0a0a0a',
        card: '#121212',
        text: '#f5f5f5',
        muted: '#a3a3a3',
        accent: '#e5e5e5',
        border: '#2a2a2a',
      },
      boxShadow: {
        glass: '0 10px 30px rgba(0,0,0,0.3)'
      },
      backdropBlur: {
        xs: '6px'
      }
    },
  },
  plugins: [],
}
