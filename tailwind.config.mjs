/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
          950: '#052e16',
        },
        stone: {
          50: '#fafaf9',
          100: '#f5f5f4',
          200: '#e7e5e4',
          300: '#d6d3d1',
          400: '#a8a29e',
          500: '#78716c',
          600: '#57534e',
          700: '#44403c',
          800: '#292524',
          900: '#1c1917',
          950: '#0c0a09',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Merriweather', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            '--tw-prose-body': theme('colors.stone.800'),
            '--tw-prose-headings': theme('colors.stone.900'),
            '--tw-prose-lead': theme('colors.stone.700'),
            '--tw-prose-links': theme('colors.primary.700'),
            '--tw-prose-bold': theme('colors.stone.900'),
            '--tw-prose-counters': theme('colors.stone.500'),
            '--tw-prose-bullets': theme('colors.stone.400'),
            '--tw-prose-hr': theme('colors.stone.200'),
            '--tw-prose-quotes': theme('colors.stone.900'),
            '--tw-prose-quote-borders': theme('colors.primary.300'),
            '--tw-prose-captions': theme('colors.stone.500'),
            '--tw-prose-code': theme('colors.primary.700'),
            '--tw-prose-pre-code': theme('colors.stone.100'),
            '--tw-prose-pre-bg': theme('colors.stone.900'),
            '--tw-prose-th-borders': theme('colors.stone.300'),
            '--tw-prose-td-borders': theme('colors.stone.200'),
            maxWidth: 'none',
          },
        },
      }),
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};