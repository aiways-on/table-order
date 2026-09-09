import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: proxy /api (REST + SSE) to the backend. The customer app authenticates
// with an X-Session-Token header (no cookie), so no credentials handling is
// needed here. Prod: nginx reverse-proxies /api instead (see nginx.conf).
const BACKEND = process.env.VITE_BACKEND_ORIGIN || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: BACKEND,
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
  },
})
