import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@/styles/index.scss'
import 'element-plus/theme-chalk/base.css'
import 'element-plus/theme-chalk/el-message.css'
import 'element-plus/theme-chalk/el-message-box.css'
import 'element-plus/theme-chalk/el-overlay.css'
import i18n from '@/locales'
import router from './router'
import './router/permission' // Permission guard
import vFocusTrap from './directives/vFocusTrap'
import App from './App.vue'
import { useBrandingStore } from '@/stores/branding'

const bootstrap = async () => {
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  app.use(i18n)
  app.use(router)
  app.directive('focus-trap', vFocusTrap)

  const brandingStore = useBrandingStore(pinia)
  // Render immediately with cached/default branding, then refresh branding in the background.
  brandingStore.applyBranding(brandingStore.settings)

  app.mount('#app')
  void brandingStore.initialize()
}

bootstrap()
