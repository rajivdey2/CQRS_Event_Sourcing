import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        base:    '#0A0F1E',
        surface: '#141929',
        border:  '#1E2940',
        muted:   '#94A3B8',
        primary: '#6366F1',
        emerald: '#10B981',
        rose:    '#F43F5E',
        amber:   '#F59E0B',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config