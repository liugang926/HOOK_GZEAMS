import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'happy-dom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'src/e2e/',
      ]
    },
    include: ['src/**/*.{test,spec}.{js,ts,vue}', 'tests/**/*.{test,spec}.{js,ts}'],
    root: '.',
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  }
})
