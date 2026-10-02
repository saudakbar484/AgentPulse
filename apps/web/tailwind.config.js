/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        neu: {
          bg: "#EEF2F6",
          surface: "#EEF2F6",
          hover: "#F4F7FB",
          recessed: "#E5EBF1",
          border: "rgba(255, 255, 255, 0.7)",
          darkBorder: "rgba(209, 217, 230, 0.4)",
        },
        brand: {
          blue: "#2563EB",
          blueHover: "#1D4ED8",
          blueGlow: "rgba(37, 99, 235, 0.28)",
          cyan: "#0EA5E9",
          slate: "#0F172A",
        }
      },
      boxShadow: {
        'neu-flat': '6px 6px 14px #D1D9E6, -6px -6px 14px #FFFFFF',
        'neu-hover': '9px 9px 20px #C5D0DE, -9px -9px 20px #FFFFFF',
        'neu-inset': 'inset 3px 3px 6px #D1D9E6, inset -3px -3px 6px #FFFFFF',
        'neu-button': '4px 4px 10px #D1D9E6, -4px -4px 10px #FFFFFF, 0 8px 18px -4px rgba(37, 99, 235, 0.35)',
        'neu-pressed': 'inset 2px 2px 5px rgba(0, 0, 0, 0.25)',
        'neu-modal': '14px 14px 28px #BAC5D6, -14px -14px 28px #FFFFFF, 0 20px 40px -10px rgba(15, 23, 42, 0.08)',
        'evidence-glow': '0 0 12px rgba(245, 158, 11, 0.35)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-radar': 'radar-pulse 2s infinite',
      },
      keyframes: {
        'radar-pulse': {
          '0%': { transform: 'scale(0.95)', boxShadow: '0 0 0 0 rgba(16, 185, 129, 0.5)' },
          '70%': { transform: 'scale(1)', boxShadow: '0 0 0 8px rgba(16, 185, 129, 0)' },
          '100%': { transform: 'scale(0.95)', boxShadow: '0 0 0 0 rgba(16, 185, 129, 0)' },
        }
      }
    },
  },
  plugins: [],
}
