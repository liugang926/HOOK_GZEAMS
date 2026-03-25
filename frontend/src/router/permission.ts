import router from '@/router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import i18n from '@/locales'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

NProgress.configure({ showSpinner: false })

const whiteList = ['/login', '/404']
const allowUnmountedModules =
  typeof window !== 'undefined' &&
  window.localStorage.getItem('VITE_ENABLE_UNMOUNTED_MODULES') === '1'
const disabledRoutePrefixes: string[] = []

const isRouteBlockedByBackendMount = (path: string): boolean => {
  if (allowUnmountedModules) return false
  return disabledRoutePrefixes.some((prefix) => path.startsWith(prefix))
}

router.beforeEach(async (to: any, _from: any, next: any) => {
  NProgress.start()
  const userStore = useUserStore()

  const hasToken = userStore.token

  if (hasToken) {
    if (to.path === '/login') {
      next({ path: '/' })
      NProgress.done()
    } else {
      if (isRouteBlockedByBackendMount(to.path)) {
        ElMessage.warning(i18n.global.t('common.messages.moduleNotEnabledRedirect'))
        next({ path: '/dashboard' })
        NProgress.done()
        return
      }

      if (userStore.roles && userStore.roles.length > 0) {
        next()
      } else {
        try {
          await userStore.getUserInfo()
          next({ ...to, replace: true })
        } catch (error) {
          userStore.logout()
          next(`/login?redirect=${to.path}`)
          NProgress.done()
        }
      }
    }
  } else {
    if (whiteList.indexOf(to.path) !== -1) {
      next()
    } else {
      next(`/login?redirect=${to.path}`)
      NProgress.done()
    }
  }
})

router.afterEach(() => {
  NProgress.done()
})
