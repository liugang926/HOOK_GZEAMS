import { prefetchComponent } from '@/utils/lazyLoad'
import { prefetchXlsx } from '@/utils/xlsxLoader'

type RoutePrefetchRegistration = {
  match: string
  loaders: Array<() => Promise<unknown>>
  warmUp?: () => void
}

type IdleRoutePrefetchRegistration = {
  match: string
  relatedPaths?: string[]
  warmUp?: () => void
}

const prefetchedKeys = new Set<string>()
const idlePrefetchedKeys = new Set<string>()

const routePrefetchRegistrations: RoutePrefetchRegistration[] = [
  {
    match: '/admin/workflows',
    loaders: [
      () => import('@/views/admin/WorkflowList.vue'),
      () => import('@/views/admin/WorkflowEdit.vue'),
      () => import('@/components/workflow/WorkflowDesigner.vue'),
    ],
  },
  {
    match: '/reports/center',
    loaders: [
      () => import('@/views/reports/ReportCenter.vue'),
    ],
    warmUp: () => {
      prefetchXlsx()
    },
  },
  {
    match: '/system/page-layouts/designer',
    loaders: [
      () => import('@/views/system/PageLayoutDesigner.vue'),
      () => import('@/components/designer/WysiwygLayoutDesigner.vue'),
    ],
  },
  {
    match: '/system/business-rules',
    loaders: [
      () => import('@/views/system/BusinessRuleList.vue'),
      () => import('@/components/designer/RuleDesigner.vue'),
    ],
  },
  {
    match: '/system/config-packages',
    loaders: [
      () => import('@/views/system/ConfigPackageList.vue'),
    ],
  },
]

const idleRoutePrefetchRegistrations: IdleRoutePrefetchRegistration[] = [
  {
    match: '/dashboard',
    relatedPaths: ['/reports/center', '/admin/workflows'],
  },
  {
    match: '/admin/workflows',
    relatedPaths: ['/admin/workflows/create'],
  },
  {
    match: '/system/page-layouts',
    relatedPaths: ['/system/page-layouts/designer'],
  },
  {
    match: '/system/business-rules',
    relatedPaths: ['/system/business-rules'],
  },
  {
    match: '/system/config-packages',
    relatedPaths: ['/system/config-packages'],
  },
  {
    match: '/reports/center',
    warmUp: () => {
      prefetchXlsx()
    },
  },
]

const normalizePath = (path: string): string => {
  const trimmed = String(path || '').trim()
  if (!trimmed) return ''
  const normalized = trimmed.startsWith('/') ? trimmed : `/${trimmed}`
  return normalized.split('?')[0].split('#')[0]
}

export const prefetchRouteResources = (path: string): void => {
  const normalizedPath = normalizePath(path)
  if (!normalizedPath) return

  const registration = routePrefetchRegistrations.find((entry) =>
    normalizedPath.startsWith(entry.match)
  )

  if (!registration) return

  const cacheKey = `${registration.match}:${normalizedPath}`
  if (prefetchedKeys.has(cacheKey)) return
  prefetchedKeys.add(cacheKey)

  for (const loader of registration.loaders) {
    prefetchComponent(loader)
  }

  registration.warmUp?.()
}

export const prefetchGroupedRouteResources = (paths: string[]): void => {
  for (const path of paths) {
    prefetchRouteResources(path)
  }
}

const scheduleIdleWork = (callback: () => void, timeout = 1200): (() => void) => {
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    const handle = window.requestIdleCallback(callback, { timeout })
    return () => window.cancelIdleCallback(handle)
  }

  const handle = globalThis.setTimeout(callback, 300)
  return () => globalThis.clearTimeout(handle)
}

export const scheduleIdleRoutePrefetch = (path: string): (() => void) => {
  const normalizedPath = normalizePath(path)
  if (!normalizedPath) return () => {}

  const registration = idleRoutePrefetchRegistrations.find((entry) =>
    normalizedPath.startsWith(entry.match)
  )

  if (!registration) return () => {}

  const cacheKey = `${registration.match}:${normalizedPath}`
  if (idlePrefetchedKeys.has(cacheKey)) return () => {}

  return scheduleIdleWork(() => {
    if (idlePrefetchedKeys.has(cacheKey)) return
    idlePrefetchedKeys.add(cacheKey)

    if (registration.relatedPaths?.length) {
      prefetchGroupedRouteResources(registration.relatedPaths)
    }

    registration.warmUp?.()
  })
}
