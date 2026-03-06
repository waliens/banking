import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { PrimeVueResolver } from '@primevue/auto-import-resolver'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    Components({
      resolvers: [PrimeVueResolver()]
    }),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Banking',
        short_name: 'Banking',
        theme_color: '#6366f1',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          { src: '/pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: '/pwa-512x512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /\/api\/v2\/categories$/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'api-categories',
              expiration: { maxAgeSeconds: 86400 },
            },
          },
          {
            urlPattern: /\/api\/v2\/accounts$/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'api-accounts',
              expiration: { maxAgeSeconds: 86400 },
            },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api/v2': {
        target: process.env.API_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
  }
})
