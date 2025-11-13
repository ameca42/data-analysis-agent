import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,  // 如果端口被占用，会报错而不是自动切换
    proxy: {
      '/upload': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/datasets': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
