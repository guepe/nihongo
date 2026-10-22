import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  // In development, the API runs with: php -S 127.0.0.1:8787 api/index.php (see app/README.md)
  server: { proxy: { '/api': 'http://127.0.0.1:8787' } },
  preview: { proxy: { '/api': 'http://127.0.0.1:8787' } },
  plugins: [
    svelte(),
    VitePWA({
      // A new version waits for the user's go-ahead, so that a review isn't interrupted.
      registerType: 'prompt',
      includeAssets: ['favicon.svg', 'apple-touch-icon.png'],
      manifest: {
        name: 'hachi — japonais',
        short_name: 'hachi',
        description: 'Révision du vocabulaire et de la conjugaison japonaise',
        lang: 'fr',
        start_url: '/',
        display: 'standalone',
        background_color: '#f7f4ee',
        theme_color: '#f7f4ee',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // deck.json is precached too: the app works offline, and a new deck comes with a
        // new version of the service worker.
        globPatterns: ['**/*.{js,css,html,svg,png,json}'],
        maximumFileSizeToCacheInBytes: 8 * 1024 * 1024,
        // The API (phase D) must always go to the network.
        navigateFallbackDenylist: [/^\/api\//],
      },
    }),
  ],
})
