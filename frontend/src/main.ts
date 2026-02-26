import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@/styles/index.scss'
import i18n from '@/locales'
import router from './router'
import './router/permission' // Permission guard
import App from './App.vue'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(i18n)
app.use(router)

// Element Plus locale will be handled reactively via locale store in App.vue
app.use(ElementPlus)

app.mount('#app')
