type TranslationFn = (key: string) => string

export const getPortalAssetStatusTagType = (status: string) => {
  const tagTypeMap: Record<string, string> = {
    in_use: 'success',
    idle: 'info',
    under_maintenance: 'warning',
    maintenance: 'warning',
    disposed: 'danger',
    scrapped: 'danger',
  }

  return tagTypeMap[status] || 'info'
}

export const getPortalAssetDetailPath = (id: string | number) => `/objects/Asset/${id}`

export const formatPortalAssetValue = (
  value: number | string | null | undefined,
  t: TranslationFn
) => {
  if (value === null || value === undefined || value === '') {
    return '-'
  }

  return `${t('common.units.yuan')} ${Number(value).toLocaleString()}`
}

export const createPortalAssetStatusOptions = (t: TranslationFn) => ([
  { value: 'in_use', label: t('portal.assets.status.inUse') },
  { value: 'idle', label: t('portal.assets.status.idle') },
  { value: 'under_maintenance', label: t('portal.assets.status.maintenance') },
  { value: 'disposed', label: t('portal.assets.status.disposed') }
])
