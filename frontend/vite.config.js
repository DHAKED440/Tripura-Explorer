import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': process.env.TRIPURA_API_ORIGIN || 'http://127.0.0.1:5000',
      '/static': process.env.TRIPURA_API_ORIGIN || 'http://127.0.0.1:5000',
      '/experiences/place-photo': process.env.TRIPURA_API_ORIGIN || 'http://127.0.0.1:5000'
    }
  }
})
