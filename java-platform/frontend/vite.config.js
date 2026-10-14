import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  root: fileURLToPath(new URL('.', import.meta.url)),
  plugins: [vue()],
  server: { proxy: { '/api': { target: 'http://127.0.0.1:8088', changeOrigin: true } } },
  build: { chunkSizeWarningLimit: 1500 }
});

