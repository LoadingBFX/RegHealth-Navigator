/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#EBF8FF',
          100: '#BEE3F8',
          200: '#90CDF4',
          300: '#63B3ED',
          400: '#4299E1',
          500: '#3182CE',
          600: '#2B6CB0',
          700: '#1A365D', // Main primary
          800: '#153E75',
          900: '#1A365D',
        },
        secondary: {
          50: '#E6FFFA',
          100: '#B2F5EA',
          200: '#81E6D9',
          300: '#4FD1C5',
          400: '#38B2AC',
          500: '#319795',
          600: '#2C7A7B', // Main secondary
          700: '#285E61',
          800: '#234E52',
          900: '#1D4044',
        },
        accent: {
          50: '#FBF6E7',
          100: '#FAF0CE',
          200: '#F6E4A3',
          300: '#F2D279',
          400: '#EEC550',
          500: '#D69E2E', // Main accent
          600: '#B7791F',
          700: '#975A16',
          800: '#744210',
          900: '#5F370E',
        },
        success: {
          50: '#F0FFF4',
          100: '#C6F6D5',
          200: '#9AE6B4',
          300: '#68D391',
          400: '#48BB78',
          500: '#38A169', // Main success
          600: '#2F855A',
          700: '#276749',
          800: '#22543D',
          900: '#1C4532',
        },
        warning: {
          50: '#FFFAF0',
          100: '#FEEBC8',
          200: '#FBD38D',
          300: '#F6AD55',
          400: '#ED8936',
          500: '#DD6B20', // Main warning
          600: '#C05621',
          700: '#9C4221',
          800: '#7B341E',
          900: '#652B19',
        },
        error: {
          50: '#FFF5F5',
          100: '#FED7D7',
          200: '#FEB2B2',
          300: '#FC8181',
          400: '#F56565',
          500: '#E53E3E', // Main error
          600: '#C53030',
          700: '#9B2C2C',
          800: '#822727',
          900: '#63171B',
        },
        neutral: {
          50: '#F7FAFC',
          100: '#EDF2F7',
          200: '#E2E8F0',
          300: '#CBD5E0',
          400: '#A0AEC0',
          500: '#718096',
          600: '#4A5568',
          700: '#2D3748',
          800: '#1A202C',
          900: '#171923',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      spacing: {
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      },
      boxShadow: {
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'nav': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
      },
    },
  },
  plugins: [],
};