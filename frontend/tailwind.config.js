/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        medical: {
          bg: '#020617',      // Very Dark Navy (Main Background)
          panel: '#0f172a',   // Slate 900 (Panel Background)
          surface: '#1e293b', // Slate 800 (Borders)
          text: '#f1f5f9',    // Slate 100 (Main Text)
          muted: '#94a3b8',   // Slate 400 (Secondary Text)

          primary: '#06b6d4', // Cyan 500 (Radiology Blue)
          accent: '#38bdf8',  // Sky 400
          success: '#10b981', // Emerald
          warning: '#f59e0b', // Amber
          danger: '#ef4444',  // Red
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'medical': '0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
        'glow': '0 0 10px rgba(6, 182, 212, 0.3)',
      }
    },
  },
  plugins: [],
}
