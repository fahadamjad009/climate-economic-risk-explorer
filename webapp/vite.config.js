import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/climate-economic-risk-explorer/',
  plugins: [react()],
  optimizeDeps: {
    include: ['prop-types'],
  },
})
