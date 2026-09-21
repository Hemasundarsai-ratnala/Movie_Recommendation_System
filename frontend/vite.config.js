import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Backend port is injected by run.py via the BACKEND_PORT env var.
// Falls back to 8000 when starting npm run dev independently.
const backendPort = process.env.BACKEND_PORT || '8000';
const backendTarget = `http://127.0.0.1:${backendPort}`;

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
})
