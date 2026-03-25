import type { StatusAction } from '@/components/common/StatusActionBar.vue'
import type { SubTableColumn } from '@/components/common/SubTablePanel.vue'

export interface SubTableConfig {
  columns: (t: (key: string) => string) => SubTableColumn[]
  fetchItems: (id: string) => Promise<any[]>
  summaryMethod?: (params: { columns: any[]; data: any[] }) => any[]
  emptyText?: string
}

export interface WorkflowStepConfig {
  steps: string[]
  i18nPrefix: string
}

export interface LifecycleDetailExtension {
  fetchDetail: (id: string) => Promise<any>
  refreshDetail: (id: string) => Promise<any>
  workflowSteps?: WorkflowStepConfig
  statusActions: (id: string, t: (key: string) => string) => StatusAction[]
  subTable?: SubTableConfig
  showCostBreakdown?: boolean
}

export interface LifecycleDetailApi {
  detail: (id: string) => Promise<any>
}

export type LifecycleDetailStatusActionFactory = (
  id: string,
  t: (key: string) => string
) => StatusAction[]
