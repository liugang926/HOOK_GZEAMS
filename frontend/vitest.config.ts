import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue(), vueJsx()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/__tests__/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/__tests__/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData/**',
        'src/main.ts',
        'src/e2e/'
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80
      },
      perFile: true
    },
    include: ['src/**/*.{test,spec}.{js,ts,vue}', 'tests/**/*.{test,spec}.{js,ts}'],
    root: '.',
    testTimeout: 10000,
    hookTimeout: 10000,
    threads: true
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  }
})
