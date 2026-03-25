import type {
  DashboardLifecycleState,
  DashboardMetricsState,
} from './dashboardModel'

type TranslationFn = (key: string) => string

export interface DashboardMetricCard {
  id: string
  label: string
  tagLabel: string
  tagType?: string
  value: string | number
  valueClass?: string
}

export interface DashboardLifecycleCard {
  id: string
  label: string
  icon: 'purchase' | 'maintenance' | 'task' | 'disposal'
  iconColor: string
  route: string
  value: string
  valueClass?: string
}

export const buildDashboardMetricCards = (
  metrics: DashboardMetricsState,
  t: TranslationFn
): DashboardMetricCard[] => ([
  {
    id: 'assetCount',
    label: t('dashboard.metrics.assetCount'),
    tagLabel: t('common.units.piece'),
    value: metrics.assetCount,
  },
  {
    id: 'assetValue',
    label: t('dashboard.metrics.assetValue'),
    tagLabel: t('common.units.yuan'),
    tagType: 'success',
    value: `${t('common.units.yuan')} ${metrics.assetValue}`,
  },
  {
    id: 'warningCount',
    label: t('dashboard.metrics.warningCount'),
    tagLabel: t('common.units.item'),
    tagType: 'danger',
    value: metrics.warningCount,
    valueClass: 'text-danger',
  },
  {
    id: 'pendingApproval',
    label: t('dashboard.metrics.pendingApproval'),
    tagLabel: t('common.units.pending'),
    tagType: 'warning',
    value: metrics.pendingApproval,
  }
])

export const buildDashboardLifecycleCards = (
  lifecycle: DashboardLifecycleState,
  loading: boolean,
  t: TranslationFn
): DashboardLifecycleCard[] => {
  const displayValue = (value: number) => (loading ? '-' : String(value))

  return [
    {
      id: 'pendingPurchases',
      label: t('dashboard.lifecycle.pendingPurchases'),
      icon: 'purchase',
      iconColor: '#409eff',
      route: '/objects/PurchaseRequest',
      value: displayValue(lifecycle.pendingPurchases),
      valueClass: 'text-primary',
    },
    {
      id: 'activeMaintenance',
      label: t('dashboard.lifecycle.activeMaintenance'),
      icon: 'maintenance',
      iconColor: '#e6a23c',
      route: '/objects/Maintenance',
      value: displayValue(lifecycle.activeMaintenance),
      valueClass: 'text-warning',
    },
    {
      id: 'overdueTasks',
      label: t('dashboard.lifecycle.overdueTasks'),
      icon: 'task',
      iconColor: '#f56c6c',
      route: '/objects/MaintenanceTask',
      value: displayValue(lifecycle.overdueTasks),
      valueClass: 'text-danger',
    },
    {
      id: 'pendingDisposals',
      label: t('dashboard.lifecycle.pendingDisposals'),
      icon: 'disposal',
      iconColor: '#909399',
      route: '/objects/DisposalRequest',
      value: displayValue(lifecycle.pendingDisposals),
    }
  ]
}
