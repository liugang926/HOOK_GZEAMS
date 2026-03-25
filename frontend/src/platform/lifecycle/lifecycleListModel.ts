import { Calendar, Warning } from '@element-plus/icons-vue'

type ButtonType = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
export type LifecycleQuickFilterMode = 'all' | 'overdue' | 'today'

export interface LifecycleListQuickFilterDefinition {
  key: LifecycleQuickFilterMode
  labelKey: string
  type?: ButtonType
  icon?: unknown
  active: boolean
}

export interface LifecycleListRowActionDefinition {
  key: string
  labelKey: string
  type?: ButtonType
}

type LifecycleListRowActionRule = LifecycleListRowActionDefinition & {
  visibleWhen: (row: Record<string, any>) => boolean
}

const lifecycleStatusTranslationPrefixMap: Record<string, string> = {
  PurchaseRequest: 'assets.lifecycle.purchaseRequest.status',
  AssetReceipt: 'assets.lifecycle.assetReceipt.status',
  Maintenance: 'assets.lifecycle.maintenance.status',
  MaintenancePlan: 'assets.lifecycle.maintenancePlan.status',
  MaintenanceTask: 'assets.lifecycle.maintenanceTask.status',
  DisposalRequest: 'assets.lifecycle.disposalRequest.status',
  AssetWarranty: 'assets.lifecycle.assetWarranty.status',
  FinanceVoucher: 'finance.status',
}

const lifecycleStatusTypeMap: Record<string, Record<string, string>> = {
  PurchaseRequest: {
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    rejected: 'danger',
    processing: 'primary',
    completed: '',
    cancelled: 'info',
  },
  AssetReceipt: {
    draft: 'info',
    submitted: 'warning',
    inspecting: 'primary',
    passed: 'success',
    rejected: 'danger',
    cancelled: 'info',
  },
  Maintenance: {
    pending: 'info',
    assigned: 'warning',
    in_progress: 'primary',
    completed: 'warning',
    verified: 'success',
    cancelled: 'info',
  },
  MaintenancePlan: {
    active: 'success',
    paused: 'warning',
    archived: 'info',
  },
  MaintenanceTask: {
    pending: 'warning',
    in_progress: 'primary',
    completed: 'success',
    verified: '',
    skipped: 'info',
  },
  DisposalRequest: {
    draft: 'info',
    submitted: 'warning',
    appraising: 'primary',
    approved: 'success',
    rejected: 'danger',
    executing: 'primary',
    completed: '',
    cancelled: 'info',
  },
  AssetWarranty: {
    draft: 'info',
    active: 'success',
    expiring: 'warning',
    expired: 'danger',
    claimed: '',
    cancelled: 'info',
  },
  FinanceVoucher: {
    draft: 'info',
    submitted: 'warning',
    approved: 'primary',
    posted: 'success',
    rejected: 'danger',
  },
}

const lifecycleQuickFilterRegistry: Record<string, Array<Omit<LifecycleListQuickFilterDefinition, 'active'>>> = {
  MaintenanceTask: [
    {
      key: 'overdue',
      labelKey: 'assets.lifecycle.maintenanceTask.filter.overdue',
      type: 'danger',
      icon: Warning,
    },
    {
      key: 'today',
      labelKey: 'assets.lifecycle.maintenanceTask.filter.today',
      type: 'primary',
      icon: Calendar,
    },
    {
      key: 'all',
      labelKey: 'assets.lifecycle.maintenanceTask.filter.all',
      type: 'default',
    },
  ],
}

const lifecycleRowActionRegistry: Record<string, LifecycleListRowActionRule[]> = {
  PurchaseRequest: [
    {
      key: 'submit',
      labelKey: 'assets.lifecycle.purchaseRequest.actions.submit',
      type: 'primary',
      visibleWhen: (row) => row.status === 'draft',
    },
    {
      key: 'cancel',
      labelKey: 'assets.lifecycle.purchaseRequest.actions.cancel',
      type: 'danger',
      visibleWhen: (row) => ['draft', 'submitted'].includes(String(row.status || '')),
    },
  ],
  AssetReceipt: [
    {
      key: 'submitInspection',
      labelKey: 'assets.lifecycle.assetReceipt.actions.submitInspection',
      type: 'primary',
      visibleWhen: (row) => row.status === 'draft',
    },
    {
      key: 'cancel',
      labelKey: 'assets.lifecycle.assetReceipt.actions.cancel',
      type: 'danger',
      visibleWhen: (row) => ['draft', 'submitted'].includes(String(row.status || '')),
    },
  ],
  Maintenance: [
    {
      key: 'cancel',
      labelKey: 'assets.lifecycle.maintenance.actions.cancel',
      type: 'danger',
      visibleWhen: (row) => ['pending', 'assigned', 'in_progress'].includes(String(row.status || '')),
    },
  ],
  MaintenancePlan: [
    {
      key: 'activate',
      labelKey: 'assets.lifecycle.maintenancePlan.actions.activate',
      type: 'success',
      visibleWhen: (row) => row.status === 'paused',
    },
    {
      key: 'pause',
      labelKey: 'assets.lifecycle.maintenancePlan.actions.pause',
      type: 'warning',
      visibleWhen: (row) => row.status === 'active',
    },
    {
      key: 'generateTasks',
      labelKey: 'assets.lifecycle.maintenancePlan.actions.generateTasks',
      type: 'info',
      visibleWhen: (row) => ['active', 'paused'].includes(String(row.status || '')),
    },
  ],
  MaintenanceTask: [
    {
      key: 'execute',
      labelKey: 'assets.lifecycle.maintenanceTask.actions.execute',
      type: 'success',
      visibleWhen: (row) => ['pending', 'in_progress'].includes(String(row.status || '')),
    },
    {
      key: 'skip',
      labelKey: 'assets.lifecycle.maintenanceTask.actions.skip',
      type: 'warning',
      visibleWhen: (row) => row.status === 'pending',
    },
  ],
  DisposalRequest: [
    {
      key: 'submit',
      labelKey: 'assets.lifecycle.disposalRequest.actions.submit',
      type: 'primary',
      visibleWhen: (row) => row.status === 'draft',
    },
    {
      key: 'cancel',
      labelKey: 'assets.lifecycle.disposalRequest.actions.cancel',
      type: 'danger',
      visibleWhen: (row) => ['draft', 'submitted'].includes(String(row.status || '')),
    },
  ],
  AssetWarranty: [
    {
      key: 'activate',
      labelKey: 'assets.lifecycle.assetWarranty.actions.activate',
      type: 'success',
      visibleWhen: (row) => row.status === 'draft',
    },
    {
      key: 'renew',
      labelKey: 'assets.lifecycle.assetWarranty.actions.renew',
      type: 'warning',
      visibleWhen: (row) => ['active', 'expiring'].includes(String(row.status || '')),
    },
    {
      key: 'cancel',
      labelKey: 'assets.lifecycle.assetWarranty.actions.cancel',
      type: 'danger',
      visibleWhen: (row) => !['cancelled', 'expired'].includes(String(row.status || '')),
    },
  ],
  FinanceVoucher: [
    {
      key: 'post',
      labelKey: 'finance.actions.post',
      type: 'success',
      visibleWhen: (row) => row.status === 'approved',
    },
    {
      key: 'retryPush',
      labelKey: 'finance.actions.retryPush',
      type: 'warning',
      visibleWhen: (row) => ['approved', 'posted'].includes(String(row.status || '')),
    },
  ],
}

export const getLifecycleListStatusTranslationKey = (objectCode: string, status: string): string | null => {
  const prefix = lifecycleStatusTranslationPrefixMap[String(objectCode || '').trim()]
  const normalizedStatus = String(status || '').trim()
  if (!prefix || !normalizedStatus) return null
  return `${prefix}.${normalizedStatus}`
}

export const getLifecycleListStatusType = (objectCode: string, status: string): string | null => {
  const normalizedObjectCode = String(objectCode || '').trim()
  const normalizedStatus = String(status || '').trim()
  if (!normalizedObjectCode || !normalizedStatus) return null
  return lifecycleStatusTypeMap[normalizedObjectCode]?.[normalizedStatus] ?? null
}

export const getLifecycleQuickFilterDefinitions = (
  objectCode: string,
  activeMode: LifecycleQuickFilterMode
): LifecycleListQuickFilterDefinition[] => {
  const definitions = lifecycleQuickFilterRegistry[String(objectCode || '').trim()] || []
  return definitions.map((definition) => ({
    ...definition,
    active: definition.key === activeMode,
  }))
}

export const getLifecycleRowActionDefinitions = (
  objectCode: string,
  row: Record<string, any>
): LifecycleListRowActionDefinition[] => {
  const rules = lifecycleRowActionRegistry[String(objectCode || '').trim()] || []
  return rules
    .filter((rule) => rule.visibleWhen(row))
    .map(({ key, labelKey, type }) => ({ key, labelKey, type }))
}
