import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/api/wallet': {
        target: 'http://localhost:8003',
        rewrite: (path) => path.replace(/^\/api\/wallet/, ''),
      },
    },
  },
})
