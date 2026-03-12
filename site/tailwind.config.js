/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#080b0f',
        surface: '#0f1318',
        'surface-2': '#161c24',
        border: '#1e2733',
        'border-bright': '#2a3545',
        accent: '#00c2ff',
        'accent-dim': '#0090cc',
        'accent-glow': 'rgba(0, 194, 255, 0.15)',
        primary: '#ffffff',
        secondary: '#8b9ab0',
        muted: '#4a5568',
        success: '#00e676',
        warning: '#ffab00',
        danger: '#ff4444',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(rgba(0,194,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,194,255,0.03) 1px, transparent 1px)",
        'hero-gradient': 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(0,194,255,0.12) 0%, transparent 60%)',
        'glow-gradient': 'radial-gradient(circle, rgba(0,194,255,0.15) 0%, transparent 70%)',
      },
      backgroundSize: {
        'grid-size': '32px 32px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { transform: 'translateY(16px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
      },
      boxShadow: {
        'glow-sm': '0 0 12px rgba(0,194,255,0.15)',
        'glow': '0 0 24px rgba(0,194,255,0.2)',
        'glow-lg': '0 0 48px rgba(0,194,255,0.25)',
        'card': '0 1px 3px rgba(0,0,0,0.5), 0 0 0 1px rgba(30,39,51,0.8)',
      },
    },
  },
  plugins: [],
};
