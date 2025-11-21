/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark Blue and White theme as requested
        primary: {
          50: '#EBF4FF',
          100: '#D1E7FF',
          200: '#A3CFFF',
          300: '#75B8FF',
          400: '#47A0FF',
          500: '#1976D2', // Main dark blue
          600: '#1565C0',
          700: '#0D47A1',
          800: '#093A82',
          900: '#052D64',
          950: '#021F45',
        },
        secondary: {
          50: '#F8FAFC',
          100: '#F1F5F9',
          200: '#E2E8F0',
          300: '#CBD5E1',
          400: '#94A3B8',
          500: '#64748B',
          600: '#475569',
          700: '#334155',
          800: '#1E293B',
          900: '#0F172A',
        },
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(25, 118, 210, 0.08)',
        'medium': '0 4px 16px rgba(25, 118, 210, 0.12)',
        'large': '0 8px 24px rgba(25, 118, 210, 0.16)',
      },
    },
  },
  plugins: [],
}
