import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      // TODO: Add proper PWA assets (favicon.ico, apple-touch-icon.png, etc.)
      includeAssets: ['vite.svg'],
      manifest: {
        name: 'Newsletter Audio Player',
        short_name: 'AudioNews',
        description: 'Listen to your AI newsletters',
        theme_color: '#ffffff',
        // TODO: Replace with proper app icons
        icons: [
          {
            src: 'vite.svg',
            sizes: '192x192',
            type: 'image/svg+xml'
          },
          {
            src: 'vite.svg',
            sizes: '512x512',
            type: 'image/svg+xml'
          }
        ]
      }
    })
  ],
})
