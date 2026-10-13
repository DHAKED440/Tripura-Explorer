/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#1B2A41',
          50: '#F0F4F8',
          100: '#D9E2EC',
          800: '#1B2A41',
          900: '#111D2E',
          950: '#0C1522',
        },
        amber: {
          DEFAULT: '#E8892B',
          light: '#F8A14E',
          dark: '#CF751D',
          bg: '#FEF6EE',
        },
        forest: {
          DEFAULT: '#2F7D4F',
          light: '#3C9761',
          dark: '#23613D',
          bg: '#EDF7F1',
        },
        cream: {
          DEFAULT: '#FAF7F2',
          card: '#F6F2EB',
          gold: '#E5CD9D',
          light: '#FFFDF9',
        },
        lake: {
          DEFAULT: '#2E8BC0',
          bg: '#EAF5FB',
        }
      },
      fontFamily: {
        sans: ['Poppins', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        'xl': '16px',
        '2xl': '20px',
        '3xl': '24px',
        '4xl': '32px',
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(27, 42, 65, 0.08)',
        'card': '0 10px 30px -5px rgba(27, 42, 65, 0.08), 0 2px 6px -1px rgba(27, 42, 65, 0.04)',
        'lift': '0 20px 35px -8px rgba(27, 42, 65, 0.16)',
      }
    },
  },
  plugins: [],
}
