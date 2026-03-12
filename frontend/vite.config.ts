import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    Components({
      dirs: [],
      dts: false,
      resolvers: [
        ElementPlusResolver({
          importStyle: 'css',
          directives: true
        })
      ]
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        // Increase timeout to prevent socket hang up errors
        proxyTimeout: 60000,
        ws: true,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('proxy error', err)
          })
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Sending request:', req.method, req.url)
          })
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log('Received response:', proxyRes.statusCode, req.url)
          })
        }
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler'
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return

          if (id.includes('element-plus')) return 'element-plus'
          if (id.includes('@element-plus/icons-vue')) return 'element-plus-icons'
          if (id.includes('echarts')) return 'echarts'
          if (id.includes('zrender')) return 'zrender'
          if (id.includes('@logicflow')) return 'logicflow'
          if (id.includes('@uppy')) return 'uppy'
          if (id.includes('vant')) return 'vant'
          if (id.includes('@zxing')) return 'zxing'

          if (
            id.includes('/vue/') ||
            id.includes('/vue-router/') ||
            id.includes('/pinia/') ||
            id.includes('/axios/')
          ) {
            return 'vendor'
          }

          return 'vendor'
        }
      }
    },
    chunkSizeWarningLimit: 950
  }
})
