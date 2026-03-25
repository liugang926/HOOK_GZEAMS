import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { resolve } from 'path'

const vendorChunkGroups: Array<{ name: string; patterns: string[] }> = [
  {
    name: 'framework',
    patterns: [
      '/vue/',
      '/@vue/',
      '/vue-router/',
      '/pinia/',
    ],
  },
  {
    name: 'http',
    patterns: [
      '/axios/',
      '/nprogress/',
    ],
  },
  {
    name: 'i18n',
    patterns: [
      '/vue-i18n/',
      '/@intlify/',
    ],
  },
  {
    name: 'utility',
    patterns: [
      '/dayjs/',
      '/lodash-es/',
      '/lodash-unified/',
      '/lodash.merge/',
      '/lodash/',
    ],
  },
  {
    name: 'storage',
    patterns: [
      '/localforage/',
    ],
  },
  {
    name: 'dragdrop',
    patterns: [
      '/sortablejs/',
    ],
  },
  {
    name: 'media',
    patterns: [
      '/viewerjs/',
      '/v-viewer/',
      '/cropperjs/',
      '/vue-cropperjs/',
      '/compressorjs/',
    ],
  },
  {
    name: 'spreadsheet',
    patterns: [
      '/xlsx/',
    ],
  },
]

const resolveVendorChunk = (id: string): string | undefined => {
  for (const group of vendorChunkGroups) {
    if (group.patterns.some((pattern) => id.includes(pattern))) {
      return group.name
    }
  }

  return undefined
}

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
          if (id.includes('@logicflow/core')) return 'logicflow-core'
          if (id.includes('@logicflow/extension')) return 'logicflow-extension'
          if (id.includes('@uppy')) return 'uppy'
          if (id.includes('vant')) return 'vant'
          if (id.includes('@zxing')) return 'zxing'

          const vendorChunk = resolveVendorChunk(id)
          if (vendorChunk) return vendorChunk

          return 'vendor'
        }
      }
    },
    chunkSizeWarningLimit: 950
  }
})
