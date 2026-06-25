import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark blue theme
        primary: {
          50: '#f0f4f8',
          100: '#d9e2f0',
          200: '#b3c5e1',
          300: '#8ca8d2',
          400: '#668bc3',
          500: '#1a2e4a', // Main dark blue
          600: '#16283f',
          700: '#122234',
          800: '#0e1c29',
          900: '#0a151f',
        },
        // Status colors
        status: {
          active: '#10b981',    // green
          pending: '#f59e0b',   // yellow
          completed: '#3b82f6', // blue
          'on-hold': '#9ca3af', // gray
        },
        // Additional semantic colors
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#3b82f6',
      },
      backgroundColor: {
        dark: '#0a0e27',
        'dark-light': '#1a2e4a',
      },
    },
  },
  plugins: [],
}

export default config
