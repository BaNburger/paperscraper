import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

function manualChunks(id: string): string | undefined {
  if (!id.includes('node_modules')) {
    return undefined
  }

  if (
    id.includes('/react/') ||
    id.includes('/react-dom/') ||
    id.includes('/react-router-dom/') ||
    id.includes('/scheduler/')
  ) {
    return 'vendor-react'
  }

  if (id.includes('@tanstack/react-query')) {
    return 'vendor-query'
  }

  if (id.includes('@radix-ui')) {
    return 'vendor-radix'
  }

  if (id.includes('@dnd-kit')) {
    return 'vendor-dnd'
  }

  if (id.includes('lucide-react')) {
    return 'vendor-icons'
  }

  if (id.includes('date-fns')) {
    return 'vendor-date'
  }

  if (id.includes('dompurify')) {
    return 'vendor-sanitize'
  }

  return undefined
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiProxyTarget = env.VITE_API_PROXY_TARGET || 'http://localhost:8000'
  const devPort = Number(env.VITE_DEV_PORT || 3000)

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    build: {
      chunkSizeWarningLimit: 550,
      rollupOptions: {
        output: {
          manualChunks,
        },
      },
    },
    server: {
      port: devPort,
      proxy: {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
