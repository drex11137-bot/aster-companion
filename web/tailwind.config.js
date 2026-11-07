/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: '#121110',
          900: '#181615',
          850: '#1C1A18',
          800: '#22201E',
          750: '#2A2724',
          700: '#332F2B',
          600: '#4D4741',
        },
        card: {
          base: '#1C1A18',
          elevated: '#22201E',
          border: '#2A2724',
          highlight: '#322E2A',
        },
        amber: {
          accent: '#E59843',
          bright: '#F5A623',
          glow: 'rgba(229, 152, 67, 0.25)',
          deep: '#C47828',
          dim: '#3A2E1D',
        },
        violet: {
          accent: '#7966F3',
          dark: '#5846D4',
          glow: 'rgba(121, 102, 243, 0.2)',
          dim: '#2A2548',
        },
        cream: {
          DEFAULT: '#FAF8F5',
          soft: '#EDE8E1',
          muted: '#A09E9B',
          dim: '#706E6B',
        },
        online: '#22C55E',
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'Helvetica',
          'Arial',
          'sans-serif',
        ],
      },
      boxShadow: {
        'amber-glow': '0 0 35px -5px rgba(229, 152, 67, 0.35)',
        'violet-glow': '0 0 35px -5px rgba(121, 102, 243, 0.35)',
        'card': '0 4px 20px -2px rgba(0, 0, 0, 0.45)',
      },
      keyframes: {
        pulseSlow: {
          '0%, 100%': { opacity: 1, transform: 'scale(1)' },
          '50%': { opacity: 0.85, transform: 'scale(1.02)' },
        },
        breathe: {
          '0%, 100%': { transform: 'scale(1)', filter: 'drop-shadow(0 0 16px rgba(229, 152, 67, 0.35))' },
          '50%': { transform: 'scale(1.03)', filter: 'drop-shadow(0 0 28px rgba(245, 166, 35, 0.6))' },
        },
      },
      animation: {
        'pulse-slow': 'pulseSlow 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'breathe': 'breathe 5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
