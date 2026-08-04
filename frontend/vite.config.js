import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/menu": "http://localhost:5000",
      "/meals": "http://localhost:5000",
      "/meal": "http://localhost:5000",
      "/grocery": "http://localhost:5000",
      "/upload-menu": "http://localhost:5000",
      "/export": "http://localhost:5000",
      "/import": "http://localhost:5000"
    }
  },
})
