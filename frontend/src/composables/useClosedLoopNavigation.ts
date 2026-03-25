import { useRouter } from 'vue-router'

export type ClosedLoopNavigationItem = {
  key?: string
  label: string
  type?: '' | 'primary' | 'success' | 'warning' | 'info' | 'danger'
  plain?: boolean
  disabled?: boolean
  visible?: boolean
  objectCode?: string
  recordId?: string
  query?: Record<string, string>
}

type CountLoaders = Record<string, () => Promise<any>>

export function useClosedLoopNavigation() {
  const router = useRouter()

  const navigateToObject = (objectCode: string, recordId: string) => {
    if (!objectCode || !recordId) return
    router.push(`/objects/${encodeURIComponent(objectCode)}/${encodeURIComponent(String(recordId))}`)
  }

  const navigateToFilteredList = (objectCode: string, query: Record<string, string>) => {
    if (!objectCode) return
    router.push({
      path: `/objects/${encodeURIComponent(objectCode)}`,
      query,
    })
  }

  const handleClosedLoopNavigation = (item: ClosedLoopNavigationItem) => {
    if (item.objectCode && item.query) {
      navigateToFilteredList(item.objectCode, item.query)
      return
    }

    if (item.objectCode && item.recordId) {
      navigateToObject(item.objectCode, item.recordId)
    }
  }

  return {
    navigateToObject,
    navigateToFilteredList,
    handleClosedLoopNavigation,
  }
}

export const readPaginatedCount = (payload: any): number => {
  return Number(payload?.count ?? payload?.data?.count ?? 0)
}

export const loadClosedLoopCounts = async <T extends Record<string, number>>(
  loaders: CountLoaders,
  fallback: T,
): Promise<T> => {
  const entries = Object.entries(loaders)

  try {
    const results = await Promise.all(entries.map(([, loader]) => loader()))
    return entries.reduce((acc, [key], index) => {
      acc[key as keyof T] = readPaginatedCount(results[index]) as T[keyof T]
      return acc
    }, { ...fallback })
  } catch {
    return { ...fallback }
  }
}
