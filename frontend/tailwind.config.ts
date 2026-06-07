import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        obsidian: '#0B0F19',
        'electric-indigo': '#4D4DFF',
        'neon-coral': '#FF6B6B',
      },
      fontFamily: {
        grotesk: ['var(--font-space-grotesk)', 'sans-serif'],
        inter: ['var(--font-inter)', 'sans-serif'],
      },
      animation: {
        'glow-pulse': 'glowPulse 2.4s ease-in-out infinite',
        'fade-slide-up': 'fadeSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both',
        'tag-appear': 'tagAppear 0.25s cubic-bezier(0.16, 1, 0.3, 1) both',
        'spin-slow': 'spin 2s linear infinite',
        'spin-reverse': 'spinReverse 1.5s linear infinite',
        'core-pulse': 'corePulse 2s ease-in-out infinite',
        'scanline': 'scanline 7s linear infinite',
        'letter-reveal': 'letterReveal 0.9s cubic-bezier(0.16, 1, 0.3, 1) both',
      },
      keyframes: {
        glowPulse: {
          '0%, 100%': {
            boxShadow: '0 0 20px rgba(77, 77, 255, 0.35), 0 0 60px rgba(77, 77, 255, 0.1)',
          },
          '50%': {
            boxShadow: '0 0 40px rgba(77, 77, 255, 0.7), 0 0 100px rgba(77, 77, 255, 0.25)',
          },
        },
        fadeSlideUp: {
          '0%': { opacity: '0', transform: 'translateY(18px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        tagAppear: {
          '0%': { opacity: '0', transform: 'scale(0.75) translateY(4px)' },
          '100%': { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
        spinReverse: {
          from: { transform: 'rotate(360deg)' },
          to: { transform: 'rotate(0deg)' },
        },
        corePulse: {
          '0%, 100%': { opacity: '0.55', transform: 'scale(0.82)' },
          '50%': { opacity: '1', transform: 'scale(1.12)' },
        },
        scanline: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '5%': { opacity: '1' },
          '95%': { opacity: '1' },
          '100%': { transform: 'translateY(100vh)', opacity: '0' },
        },
        letterReveal: {
          '0%': {
            opacity: '0',
            transform: 'translateY(44px) scale(0.88)',
            filter: 'blur(12px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0) scale(1)',
            filter: 'blur(0)',
          },
        },
      },
      backdropBlur: {
        xs: '2px',
        glass: '24px',
      },
      backgroundImage: {
        'grid-pattern':
          "linear-gradient(rgba(77,77,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(77,77,255,0.04) 1px, transparent 1px)",
        'radial-depth':
          'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(77,77,255,0.13) 0%, transparent 68%)',
      },
      backgroundSize: {
        grid: '40px 40px',
      },
    },
  },
  plugins: [],
}

export default config
