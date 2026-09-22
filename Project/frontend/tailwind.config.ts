import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e8f4fd',
          100: '#c6e4f9',
          200: '#9ecef4',
          300: '#6cb7ee',
          400: '#3da0e8',
          500: '#1a8ad3',
          600: '#0d70b0',
          700: '#0d5c8c',
          800: '#0a4a70',
          900: '#073859',
        },
        secondary: {
          500: '#27ae60',
          600: '#219a52',
          700: '#1a7a42',
        },
        water: {
          50: '#e0f7fa',
          100: '#b2ebf2',
          500: '#00bcd4',
          600: '#00acc1',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'water-drop': 'waterDrop 2s ease-in-out infinite',
        'flow': 'flow 3s linear infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
      keyframes: {
        waterDrop: {
          '0%, 100%': { transform: 'translateY(0) scale(1)', opacity: '1' },
          '50%': { transform: 'translateY(10px) scale(0.95)', opacity: '0.8' },
        },
        flow: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '200% 50%' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
