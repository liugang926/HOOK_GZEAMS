import {
  assetReceiptCrudApi,
  assetWarrantyCrudApi,
  disposalRequestCrudApi,
  maintenanceCrudApi,
  maintenancePlanCrudApi,
  maintenanceTaskCrudApi,
  purchaseRequestCrudApi
} from '@/api/lifecycleCrudAdapters'

import { resolveLifecycleDetailStatusActions } from './lifecycleDetailActions'
import { lifecycleSubTableRegistry } from './lifecycleDetailSubtables'
import type {
  LifecycleDetailApi,
  LifecycleDetailExtension,
  WorkflowStepConfig
} from './lifecycleDetailTypes'

const lifecycleDetailApiRegistry: Record<string, LifecycleDetailApi> = {
  PurchaseRequest: purchaseRequestCrudApi,
  AssetReceipt: assetReceiptCrudApi,
  Maintenance: maintenanceCrudApi,
  MaintenancePlan: maintenancePlanCrudApi,
  MaintenanceTask: maintenanceTaskCrudApi,
  DisposalRequest: disposalRequestCrudApi,
  AssetWarranty: assetWarrantyCrudApi,
}

const lifecycleWorkflowStepRegistry: Partial<Record<string, WorkflowStepConfig>> = {
  PurchaseRequest: {
    steps: ['draft', 'submitted', 'approved', 'processing', 'completed'],
    i18nPrefix: 'assets.lifecycle.purchaseRequest.status'
  },
  AssetReceipt: {
    steps: ['draft', 'submitted', 'inspecting', 'passed'],
    i18nPrefix: 'assets.lifecycle.assetReceipt.status'
  },
  Maintenance: {
    steps: ['pending', 'assigned', 'in_progress', 'completed', 'verified'],
    i18nPrefix: 'assets.lifecycle.maintenance.status'
  },
  MaintenanceTask: {
    steps: ['pending', 'in_progress', 'completed', 'verified'],
    i18nPrefix: 'assets.lifecycle.maintenanceTask.status'
  },
  DisposalRequest: {
    steps: ['draft', 'submitted', 'appraising', 'approved', 'completed'],
    i18nPrefix: 'assets.lifecycle.disposalRequest.status'
  },
}

const lifecycleCostBreakdownObjectCodes = new Set(['Maintenance'])

const createLifecycleDetailAccessors = (api: LifecycleDetailApi) => ({
  fetchDetail: (id: string) => api.detail(id),
  refreshDetail: (id: string) => api.detail(id),
})

export const lifecycleExtensionRegistry: Record<string, LifecycleDetailExtension> = Object.fromEntries(
  Object.entries(lifecycleDetailApiRegistry).map(([objectCode, api]) => {
    const workflowSteps = lifecycleWorkflowStepRegistry[objectCode]
    const subTable = lifecycleSubTableRegistry[objectCode]
    const extension: LifecycleDetailExtension = {
      ...createLifecycleDetailAccessors(api),
      statusActions: (id, t) => resolveLifecycleDetailStatusActions(objectCode, id, t),
      ...(workflowSteps ? { workflowSteps } : {}),
      ...(subTable ? { subTable } : {}),
      ...(lifecycleCostBreakdownObjectCodes.has(objectCode) ? { showCostBreakdown: true } : {}),
    }
    return [objectCode, extension]
  })
) as Record<string, LifecycleDetailExtension>

export function hasLifecycleExtension(objectCode: string): boolean {
  return !!lifecycleExtensionRegistry[String(objectCode || '').trim()]
}

export function getLifecycleExtension(objectCode: string): LifecycleDetailExtension | null {
  return lifecycleExtensionRegistry[String(objectCode || '').trim()] || null
}
