import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#17202a',
        mist: '#eef4f3',
        cedar: '#0f766e',
        coral: '#b4533a',
      },
    },
  },
  plugins: [],
} satisfies Config;
