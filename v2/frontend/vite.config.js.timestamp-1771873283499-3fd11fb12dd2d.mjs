// vite.config.js
import { defineConfig } from "file:///app/node_modules/vite/dist/node/index.js";
import vue from "file:///app/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import Components from "file:///app/node_modules/unplugin-vue-components/dist/vite.js";
import { PrimeVueResolver } from "file:///app/node_modules/@primevue/auto-import-resolver/index.mjs";
import { VitePWA } from "file:///app/node_modules/vite-plugin-pwa/dist/index.js";
var vite_config_default = defineConfig({
  plugins: [
    vue(),
    Components({
      resolvers: [PrimeVueResolver()]
    }),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Banking",
        short_name: "Banking",
        theme_color: "#6366f1",
        background_color: "#ffffff",
        display: "standalone",
        icons: [
          { src: "/pwa-192x192.png", sizes: "192x192", type: "image/png" },
          { src: "/pwa-512x512.png", sizes: "512x512", type: "image/png" }
        ]
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /\/api\/v2\/categories$/,
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "api-categories",
              expiration: { maxAgeSeconds: 86400 }
            }
          },
          {
            urlPattern: /\/api\/v2\/accounts$/,
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "api-accounts",
              expiration: { maxAgeSeconds: 86400 }
            }
          }
        ]
      }
    })
  ],
  server: {
    port: 5173,
    proxy: {
      "/api/v2": {
        target: process.env.API_URL || "http://localhost:8000",
        changeOrigin: true
      }
    }
  },
  test: {
    environment: "happy-dom",
    globals: true,
    setupFiles: ["./tests/setup.js"]
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvYXBwXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCIvYXBwL3ZpdGUuY29uZmlnLmpzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9hcHAvdml0ZS5jb25maWcuanNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXG5pbXBvcnQgQ29tcG9uZW50cyBmcm9tICd1bnBsdWdpbi12dWUtY29tcG9uZW50cy92aXRlJ1xuaW1wb3J0IHsgUHJpbWVWdWVSZXNvbHZlciB9IGZyb20gJ0BwcmltZXZ1ZS9hdXRvLWltcG9ydC1yZXNvbHZlcidcbmltcG9ydCB7IFZpdGVQV0EgfSBmcm9tICd2aXRlLXBsdWdpbi1wd2EnXG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFtcbiAgICB2dWUoKSxcbiAgICBDb21wb25lbnRzKHtcbiAgICAgIHJlc29sdmVyczogW1ByaW1lVnVlUmVzb2x2ZXIoKV1cbiAgICB9KSxcbiAgICBWaXRlUFdBKHtcbiAgICAgIHJlZ2lzdGVyVHlwZTogJ2F1dG9VcGRhdGUnLFxuICAgICAgbWFuaWZlc3Q6IHtcbiAgICAgICAgbmFtZTogJ0JhbmtpbmcnLFxuICAgICAgICBzaG9ydF9uYW1lOiAnQmFua2luZycsXG4gICAgICAgIHRoZW1lX2NvbG9yOiAnIzYzNjZmMScsXG4gICAgICAgIGJhY2tncm91bmRfY29sb3I6ICcjZmZmZmZmJyxcbiAgICAgICAgZGlzcGxheTogJ3N0YW5kYWxvbmUnLFxuICAgICAgICBpY29uczogW1xuICAgICAgICAgIHsgc3JjOiAnL3B3YS0xOTJ4MTkyLnBuZycsIHNpemVzOiAnMTkyeDE5MicsIHR5cGU6ICdpbWFnZS9wbmcnIH0sXG4gICAgICAgICAgeyBzcmM6ICcvcHdhLTUxMng1MTIucG5nJywgc2l6ZXM6ICc1MTJ4NTEyJywgdHlwZTogJ2ltYWdlL3BuZycgfSxcbiAgICAgICAgXSxcbiAgICAgIH0sXG4gICAgICB3b3JrYm94OiB7XG4gICAgICAgIHJ1bnRpbWVDYWNoaW5nOiBbXG4gICAgICAgICAge1xuICAgICAgICAgICAgdXJsUGF0dGVybjogL1xcL2FwaVxcL3YyXFwvY2F0ZWdvcmllcyQvLFxuICAgICAgICAgICAgaGFuZGxlcjogJ1N0YWxlV2hpbGVSZXZhbGlkYXRlJyxcbiAgICAgICAgICAgIG9wdGlvbnM6IHtcbiAgICAgICAgICAgICAgY2FjaGVOYW1lOiAnYXBpLWNhdGVnb3JpZXMnLFxuICAgICAgICAgICAgICBleHBpcmF0aW9uOiB7IG1heEFnZVNlY29uZHM6IDg2NDAwIH0sXG4gICAgICAgICAgICB9LFxuICAgICAgICAgIH0sXG4gICAgICAgICAge1xuICAgICAgICAgICAgdXJsUGF0dGVybjogL1xcL2FwaVxcL3YyXFwvYWNjb3VudHMkLyxcbiAgICAgICAgICAgIGhhbmRsZXI6ICdTdGFsZVdoaWxlUmV2YWxpZGF0ZScsXG4gICAgICAgICAgICBvcHRpb25zOiB7XG4gICAgICAgICAgICAgIGNhY2hlTmFtZTogJ2FwaS1hY2NvdW50cycsXG4gICAgICAgICAgICAgIGV4cGlyYXRpb246IHsgbWF4QWdlU2Vjb25kczogODY0MDAgfSxcbiAgICAgICAgICAgIH0sXG4gICAgICAgICAgfSxcbiAgICAgICAgXSxcbiAgICAgIH0sXG4gICAgfSksXG4gIF0sXG4gIHNlcnZlcjoge1xuICAgIHBvcnQ6IDUxNzMsXG4gICAgcHJveHk6IHtcbiAgICAgICcvYXBpL3YyJzoge1xuICAgICAgICB0YXJnZXQ6IHByb2Nlc3MuZW52LkFQSV9VUkwgfHwgJ2h0dHA6Ly9sb2NhbGhvc3Q6ODAwMCcsXG4gICAgICAgIGNoYW5nZU9yaWdpbjogdHJ1ZVxuICAgICAgfVxuICAgIH1cbiAgfSxcbiAgdGVzdDoge1xuICAgIGVudmlyb25tZW50OiAnaGFwcHktZG9tJyxcbiAgICBnbG9iYWxzOiB0cnVlLFxuICAgIHNldHVwRmlsZXM6IFsnLi90ZXN0cy9zZXR1cC5qcyddLFxuICB9XG59KVxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUE4TCxTQUFTLG9CQUFvQjtBQUMzTixPQUFPLFNBQVM7QUFDaEIsT0FBTyxnQkFBZ0I7QUFDdkIsU0FBUyx3QkFBd0I7QUFDakMsU0FBUyxlQUFlO0FBRXhCLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVM7QUFBQSxJQUNQLElBQUk7QUFBQSxJQUNKLFdBQVc7QUFBQSxNQUNULFdBQVcsQ0FBQyxpQkFBaUIsQ0FBQztBQUFBLElBQ2hDLENBQUM7QUFBQSxJQUNELFFBQVE7QUFBQSxNQUNOLGNBQWM7QUFBQSxNQUNkLFVBQVU7QUFBQSxRQUNSLE1BQU07QUFBQSxRQUNOLFlBQVk7QUFBQSxRQUNaLGFBQWE7QUFBQSxRQUNiLGtCQUFrQjtBQUFBLFFBQ2xCLFNBQVM7QUFBQSxRQUNULE9BQU87QUFBQSxVQUNMLEVBQUUsS0FBSyxvQkFBb0IsT0FBTyxXQUFXLE1BQU0sWUFBWTtBQUFBLFVBQy9ELEVBQUUsS0FBSyxvQkFBb0IsT0FBTyxXQUFXLE1BQU0sWUFBWTtBQUFBLFFBQ2pFO0FBQUEsTUFDRjtBQUFBLE1BQ0EsU0FBUztBQUFBLFFBQ1AsZ0JBQWdCO0FBQUEsVUFDZDtBQUFBLFlBQ0UsWUFBWTtBQUFBLFlBQ1osU0FBUztBQUFBLFlBQ1QsU0FBUztBQUFBLGNBQ1AsV0FBVztBQUFBLGNBQ1gsWUFBWSxFQUFFLGVBQWUsTUFBTTtBQUFBLFlBQ3JDO0FBQUEsVUFDRjtBQUFBLFVBQ0E7QUFBQSxZQUNFLFlBQVk7QUFBQSxZQUNaLFNBQVM7QUFBQSxZQUNULFNBQVM7QUFBQSxjQUNQLFdBQVc7QUFBQSxjQUNYLFlBQVksRUFBRSxlQUFlLE1BQU07QUFBQSxZQUNyQztBQUFBLFVBQ0Y7QUFBQSxRQUNGO0FBQUEsTUFDRjtBQUFBLElBQ0YsQ0FBQztBQUFBLEVBQ0g7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQSxNQUNMLFdBQVc7QUFBQSxRQUNULFFBQVEsUUFBUSxJQUFJLFdBQVc7QUFBQSxRQUMvQixjQUFjO0FBQUEsTUFDaEI7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUFBLEVBQ0EsTUFBTTtBQUFBLElBQ0osYUFBYTtBQUFBLElBQ2IsU0FBUztBQUFBLElBQ1QsWUFBWSxDQUFDLGtCQUFrQjtBQUFBLEVBQ2pDO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
