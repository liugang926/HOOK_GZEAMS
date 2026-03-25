type TranslationFn = (key: string) => string

export interface PortalHeaderStat {
  id: string
  label: string
  tone?: 'danger'
  value: number
}

export const getPortalDisplayName = (userInfo: Record<string, any> | null | undefined) => {
  return userInfo?.fullName || userInfo?.username || ''
}

export const getPortalUserInitial = (displayName: string) => {
  return displayName.charAt(0).toUpperCase() || 'U'
}

export const buildPortalHeaderStats = (
  counts: {
    assets: number
    pendingRequests: number
    pendingTasks: number
  },
  t: TranslationFn
): PortalHeaderStat[] => ([
  {
    id: 'assets',
    label: t('portal.stats.assets'),
    value: counts.assets,
  },
  {
    id: 'pendingRequests',
    label: t('portal.stats.pendingRequests'),
    value: counts.pendingRequests,
  },
  {
    id: 'pendingTasks',
    label: t('portal.stats.pendingTasks'),
    tone: 'danger',
    value: counts.pendingTasks,
  }
])
