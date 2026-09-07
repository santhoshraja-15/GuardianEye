import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Proxying HTTP alone does not forward WebSocket upgrade requests —
        // without this, the realtime connection (/api/v1/ws/events) hits
        // Vite's dev server directly, which has no such endpoint and closes
        // it immediately, so realtime updates silently never work under
        // `npm run dev`.
        ws: true,
      },
    },
  },
})
