export interface DashboardMetricsState {
  assetCount: number
  assetValue: string
  warningCount: number
  pendingApproval: number
}

export interface DashboardLifecycleState {
  pendingPurchases: number
  activeMaintenance: number
  overdueTasks: number
  pendingDisposals: number
}

export interface DashboardActivityItem {
  id: string
  type: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  title: string
  sub: string
  time: string
  url: string
}

type TranslationFn = (key: string) => string
type LifecycleRecord = Record<string, any>

interface ActivityConfig {
  idPrefix: string
  type: DashboardActivityItem['type']
  titleKey: string
  statusKey: string
  objectCode: string
  numberKeys: string[]
}

const lifecycleActivityConfig: Record<'purchase' | 'maintenance' | 'disposal', ActivityConfig> = {
  purchase: {
    idPrefix: 'pr',
    type: 'primary',
    titleKey: 'assets.lifecycle.purchaseRequest.title',
    statusKey: 'assets.lifecycle.purchaseRequest.status.submitted',
    objectCode: 'PurchaseRequest',
    numberKeys: ['requestNo', 'request_no'],
  },
  maintenance: {
    idPrefix: 'mt',
    type: 'warning',
    titleKey: 'assets.lifecycle.maintenance.title',
    statusKey: 'assets.lifecycle.maintenance.status.processing',
    objectCode: 'Maintenance',
    numberKeys: ['maintenanceNo', 'maintenance_no'],
  },
  disposal: {
    idPrefix: 'dr',
    type: 'danger',
    titleKey: 'assets.lifecycle.disposalRequest.title',
    statusKey: 'assets.lifecycle.disposalRequest.status.submitted',
    objectCode: 'DisposalRequest',
    numberKeys: ['requestNo', 'request_no'],
  },
}

export const createDashboardMetricsState = (): DashboardMetricsState => ({
  assetCount: 0,
  assetValue: '0',
  warningCount: 0,
  pendingApproval: 0,
})

export const createDashboardLifecycleState = (): DashboardLifecycleState => ({
  pendingPurchases: 0,
  activeMaintenance: 0,
  overdueTasks: 0,
  pendingDisposals: 0,
})

const getRecordNumber = (record: LifecycleRecord, keys: string[]) => {
  for (const key of keys) {
    const value = record?.[key]
    if (value !== undefined && value !== null && `${value}`.trim()) {
      return String(value)
    }
  }
  return ''
}

const getRecordTime = (record: LifecycleRecord) => {
  return String(record?.createdAt || record?.created_at || '')
}

const createActivityTitle = (label: string, recordNumber: string) => {
  return recordNumber ? `${label} ${recordNumber}` : label
}

const buildDashboardActivities = (
  kind: keyof typeof lifecycleActivityConfig,
  records: LifecycleRecord[],
  t: TranslationFn
): DashboardActivityItem[] => {
  const config = lifecycleActivityConfig[kind]
  return records.map((record) => {
    const recordNumber = getRecordNumber(record, config.numberKeys)
    return {
      id: `${config.idPrefix}-${record.id}`,
      type: config.type,
      title: createActivityTitle(t(config.titleKey), recordNumber),
      sub: t(config.statusKey),
      time: getRecordTime(record),
      url: `/objects/${config.objectCode}/${record.id}`,
    }
  })
}

export const buildPurchaseRequestActivities = (records: LifecycleRecord[], t: TranslationFn) =>
  buildDashboardActivities('purchase', records, t)

export const buildMaintenanceActivities = (records: LifecycleRecord[], t: TranslationFn) =>
  buildDashboardActivities('maintenance', records, t)

export const buildDisposalActivities = (records: LifecycleRecord[], t: TranslationFn) =>
  buildDashboardActivities('disposal', records, t)

export const normalizeOverdueTaskCount = (response: any) => {
  if (Array.isArray(response)) {
    return response.length
  }
  if (Array.isArray(response?.data)) {
    return response.data.length
  }
  return 0
}

export const sortDashboardActivities = (
  activities: DashboardActivityItem[],
  limit = 6
) => {
  return [...activities]
    .sort((left, right) => right.time.localeCompare(left.time))
    .slice(0, limit)
}

export const buildDashboardMaintenanceSeries = (
  lifecycle: DashboardLifecycleState,
  t: TranslationFn
) => {
  return [
    {
      value: lifecycle.activeMaintenance,
      name: t('dashboard.lifecycle.activeMaintenance'),
      itemStyle: { color: '#E6A23C' },
    },
    {
      value: lifecycle.overdueTasks,
      name: t('dashboard.lifecycle.overdueTasks'),
      itemStyle: { color: '#F56C6C' },
    },
    {
      value: lifecycle.pendingPurchases,
      name: t('dashboard.lifecycle.pendingPurchases'),
      itemStyle: { color: '#409EFF' },
    },
    {
      value: lifecycle.pendingDisposals,
      name: t('dashboard.lifecycle.pendingDisposals'),
      itemStyle: { color: '#909399' },
    }
  ].filter((item) => item.value > 0)
}

export const buildDashboardStatusSeries = (
  data: Record<string, number>,
  t: TranslationFn
) => {
  const statusMap: Record<string, { label: string; color: string }> = {
    idle: { label: t('assets.status.idle'), color: '#67C23A' },
    in_use: { label: t('assets.status.inUse'), color: '#409EFF' },
    maintenance: { label: t('assets.status.maintenance'), color: '#E6A23C' },
    scrapped: { label: t('assets.status.scrapped'), color: '#909399' },
    borrowed: { label: t('assets.status.borrowed'), color: '#6f7ad3' },
    disposed: { label: t('assets.status.disposed'), color: '#F56C6C' }
  }

  return Object.entries(data).map(([key, value]) => ({
    value,
    name: statusMap[key]?.label || key,
    itemStyle: { color: statusMap[key]?.color }
  }))
}
