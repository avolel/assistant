import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      // Forward /api requests to the FastAPI backend during dev (npm run dev).
      "/api": "http://localhost:8000",
    },
  },
})
