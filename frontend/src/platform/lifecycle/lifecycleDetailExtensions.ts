/**
 * Lifecycle Detail Extension Registry
 *
 * Maps lifecycle object codes to their workflow-specific UI configurations.
 * These extensions are consumed by LifecycleDetailRenderer to inject
 * StatusActionBar, el-steps, SubTablePanel, and extra panels into the
 * dynamic detail page via BaseDetailPage's extension slots.
 */

import type { StatusAction } from '@/components/common/StatusActionBar.vue'
import type { SubTableColumn } from '@/components/common/SubTablePanel.vue'
import {
    purchaseRequestApi,
    assetReceiptApi,
    maintenanceApi,
    maintenancePlanApi,
    maintenanceTaskApi,
    disposalRequestApi
} from '@/api/lifecycle'

// ─── Types ─────────────────────────────────────────────────────────────────────

export interface SubTableConfig {
    columns: (t: (key: string) => string) => SubTableColumn[]
    fetchItems: (id: string) => Promise<any[]>
    summaryMethod?: (params: { columns: any[]; data: any[] }) => any[]
    emptyText?: string
}

export interface WorkflowStepConfig {
    /** Ordered status keys for el-steps */
    steps: string[]
    /** i18n key prefix for step labels, e.g. 'assets.lifecycle.purchaseRequest.status' */
    i18nPrefix: string
}

export interface LifecycleDetailExtension {
    /** API detail fetcher */
    fetchDetail: (id: string) => Promise<any>
    /** Callback after successful action — receives record id, returns refreshed data */
    refreshDetail: (id: string) => Promise<any>
    /** Workflow steps for el-steps component */
    workflowSteps?: WorkflowStepConfig
    /** StatusActionBar actions factory */
    statusActions: (id: string, t: (key: string) => string) => StatusAction[]
    /** Sub-table (line items) configuration */
    subTable?: SubTableConfig
    /** Whether the cost breakdown panel should show */
    showCostBreakdown?: boolean
}

// ─── Registry ─────────────────────────────────────────────────────────────────

export const lifecycleExtensionRegistry: Record<string, LifecycleDetailExtension> = {
    PurchaseRequest: {
        fetchDetail: (id) => purchaseRequestApi.detail(id),
        refreshDetail: (id) => purchaseRequestApi.detail(id),
        workflowSteps: {
            steps: ['draft', 'submitted', 'approved', 'processing', 'completed'],
            i18nPrefix: 'assets.lifecycle.purchaseRequest.status'
        },
        statusActions: (id, t) => [
            {
                key: 'submit',
                label: t('assets.lifecycle.purchaseRequest.actions.submit'),
                type: 'primary',
                confirmMessage: t('assets.lifecycle.purchaseRequest.actions.submit') + '?',
                apiCall: () => purchaseRequestApi.submit(id),
                visibleWhen: (s) => s === 'draft',
            },
            {
                key: 'approve',
                label: t('assets.lifecycle.purchaseRequest.actions.approve'),
                type: 'success',
                confirmMessage: t('assets.lifecycle.purchaseRequest.actions.approve') + '?',
                apiCall: () => purchaseRequestApi.approve(id, 'approved'),
                visibleWhen: (s) => s === 'submitted',
            },
            {
                key: 'reject',
                label: t('assets.lifecycle.purchaseRequest.actions.reject'),
                type: 'danger',
                confirmMessage: t('assets.lifecycle.purchaseRequest.actions.reject') + '?',
                confirmType: 'warning',
                apiCall: () => purchaseRequestApi.approve(id, 'rejected'),
                visibleWhen: (s) => s === 'submitted',
            },
            {
                key: 'complete',
                label: t('assets.lifecycle.purchaseRequest.actions.complete'),
                type: 'success',
                confirmMessage: t('common.actions.complete') + '?',
                apiCall: () => purchaseRequestApi.complete(id),
                visibleWhen: (s) => s === 'processing',
            },
            {
                key: 'cancel',
                label: t('assets.lifecycle.purchaseRequest.actions.cancel'),
                type: 'default',
                confirmMessage: t('assets.lifecycle.purchaseRequest.messages.cancelConfirm'),
                confirmType: 'warning',
                apiCall: () => purchaseRequestApi.cancel(id),
                visibleWhen: (s) => ['draft', 'submitted'].includes(s),
            },
        ],
        subTable: {
            columns: (t) => [
                { prop: 'itemName', label: t('assets.lifecycle.purchaseRequest.form.assetName') },
                { prop: 'specification', label: t('assets.lifecycle.purchaseRequest.form.specification'), width: 160 },
                { prop: 'quantity', label: t('assets.lifecycle.purchaseRequest.form.quantity'), width: 100, align: 'right' },
                { prop: 'unitPrice', label: t('assets.lifecycle.purchaseRequest.form.estimatedUnitPrice'), width: 130, align: 'right' },
                { prop: 'totalAmount', label: t('assets.lifecycle.purchaseRequest.columns.totalAmount'), width: 130, align: 'right' },
                { prop: 'suggestedSupplier', label: t('assets.lifecycle.purchaseRequest.form.supplier'), width: 140 },
                { prop: 'remark', label: t('assets.lifecycle.purchaseRequest.form.remark') },
            ],
            fetchItems: (id) => purchaseRequestApi.items(id).then((r: any) => r?.results || r || []),
            summaryMethod: ({ columns, data }) =>
                columns.map((col: any, index: number) => {
                    if (index === 0) return ''
                    if (col.property === 'totalAmount') {
                        const sum = data.reduce((acc, row) => acc + (Number(row.totalAmount) || 0), 0)
                        return `¥ ${sum.toFixed(2)}`
                    }
                    if (col.property === 'quantity') {
                        return data.reduce((acc, row) => acc + (Number(row.quantity) || 0), 0)
                    }
                    return ''
                }),
        },
    },

    AssetReceipt: {
        fetchDetail: (id) => assetReceiptApi.detail(id),
        refreshDetail: (id) => assetReceiptApi.detail(id),
        workflowSteps: {
            steps: ['draft', 'submitted', 'inspecting', 'passed'],
            i18nPrefix: 'assets.lifecycle.assetReceipt.status'
        },
        statusActions: (id, t) => [
            {
                key: 'submitInspection',
                label: t('assets.lifecycle.assetReceipt.actions.submitInspection'),
                type: 'primary',
                confirmMessage: t('assets.lifecycle.assetReceipt.actions.submitInspection') + '?',
                apiCall: () => assetReceiptApi.submitInspection(id),
                visibleWhen: (s) => s === 'draft',
            },
            {
                key: 'inspect',
                label: t('assets.lifecycle.assetReceipt.actions.inspect'),
                type: 'success',
                confirmMessage: t('assets.lifecycle.assetReceipt.actions.inspect') + '?',
                apiCall: () => assetReceiptApi.inspect(id, '', true),
                visibleWhen: (s) => s === 'inspecting',
            },
            {
                key: 'generateAssets',
                label: t('assets.lifecycle.assetReceipt.actions.generateAssets'),
                type: 'success',
                confirmMessage: t('assets.lifecycle.assetReceipt.actions.generateAssets') + '?',
                apiCall: () => assetReceiptApi.generateAssets(id),
                visibleWhen: (s) => s === 'passed',
            },
            {
                key: 'cancel',
                label: t('common.actions.cancel'),
                type: 'default',
                confirmMessage: t('common.messages.confirmCancel'),
                confirmType: 'warning',
                apiCall: () => assetReceiptApi.cancel(id),
                visibleWhen: (s) => ['draft', 'submitted'].includes(s),
            },
        ],
        subTable: {
            columns: (t) => [
                { prop: 'assetDisplay', label: t('assets.lifecycle.assetReceipt.form.assetName') },
                { prop: 'quantity', label: t('assets.lifecycle.purchaseRequest.form.quantity'), width: 100, align: 'right' },
                { prop: 'inspectionResult', label: t('assets.lifecycle.assetReceipt.form.inspectionResult'), width: 140 },
            ],
            fetchItems: (id) => assetReceiptApi.items(id).then((r: any) => r?.results || r || []),
        },
    },

    Maintenance: {
        fetchDetail: (id) => maintenanceApi.detail(id),
        refreshDetail: (id) => maintenanceApi.detail(id),
        workflowSteps: {
            steps: ['pending', 'assigned', 'in_progress', 'completed', 'verified'],
            i18nPrefix: 'assets.lifecycle.maintenance.status'
        },
        statusActions: (id, t) => [
            {
                key: 'assign',
                label: t('assets.lifecycle.maintenance.actions.assign'),
                type: 'primary',
                confirmMessage: t('assets.lifecycle.maintenance.actions.assign') + '?',
                apiCall: () => maintenanceApi.assign(id, ''),
                visibleWhen: (s) => s === 'pending',
            },
            {
                key: 'startWork',
                label: t('assets.lifecycle.maintenance.actions.startWork'),
                type: 'primary',
                confirmMessage: t('assets.lifecycle.maintenance.actions.startWork') + '?',
                apiCall: () => maintenanceApi.startWork(id),
                visibleWhen: (s) => s === 'assigned',
            },
            {
                key: 'complete',
                label: t('assets.lifecycle.maintenance.actions.complete'),
                type: 'success',
                confirmMessage: t('assets.lifecycle.maintenance.actions.complete') + '?',
                apiCall: () => maintenanceApi.completeWork(id, {}),
                visibleWhen: (s) => s === 'in_progress',
            },
            {
                key: 'verify',
                label: t('assets.lifecycle.maintenance.actions.verify'),
                type: 'success',
                confirmMessage: t('assets.lifecycle.maintenance.actions.verify') + '?',
                apiCall: () => maintenanceApi.verify(id, 'approved'),
                visibleWhen: (s) => s === 'completed',
            },
            {
                key: 'cancel',
                label: t('common.actions.cancel'),
                type: 'default',
                confirmMessage: t('common.messages.confirmCancel'),
                confirmType: 'warning',
                apiCall: () => maintenanceApi.cancel(id),
                visibleWhen: (s) => ['pending', 'assigned'].includes(s),
            },
        ],
        showCostBreakdown: true,
    },

    MaintenancePlan: {
        fetchDetail: (id) => maintenancePlanApi.detail(id),
        refreshDetail: (id) => maintenancePlanApi.detail(id),
        statusActions: (id, t) => [
            {
                key: 'activate',
                label: t('assets.lifecycle.maintenancePlan.actions.activate'),
                type: 'success',
                confirmMessage: t('assets.lifecycle.maintenancePlan.actions.activate') + '?',
                apiCall: () => maintenancePlanApi.activate(id),
                visibleWhen: (s) => s === 'draft',
            },
            {
                key: 'pause',
                label: t('assets.lifecycle.maintenancePlan.actions.pause'),
                type: 'warning',
                confirmMessage: t('assets.lifecycle.maintenancePlan.actions.pause') + '?',
                apiCall: () => maintenancePlanApi.pause(id),
                visibleWhen: (s) => s === 'active',
            },
            {
                key: 'generateTasks',
                label: t('assets.lifecycle.maintenancePlan.actions.generateTasks'),
                type: 'primary',
                confirmMessage: t('assets.lifecycle.maintenancePlan.actions.generateTasks') + '?',
                apiCall: () => maintenancePlanApi.generateTasks(id),
                visibleWhen: (s) => s === 'active',
            },
        ],
    },

    MaintenanceTask: {
        fetchDetail: (id) => maintenanceTaskApi.detail(id),
        refreshDetail: (id) => maintenanceTaskApi.detail(id),
        workflowSteps: {
            steps: ['pending', 'in_progress', 'completed', 'verified'],
            i18nPrefix: 'assets.lifecycle.maintenanceTask.status'
        },
        statusActions: (id, t) => [
            {
                key: 'execute',
                label: t('assets.lifecycle.maintenanceTask.actions.execute'),
                type: 'primary',
                confirmMessage: t('assets.lifecycle.maintenanceTask.actions.execute') + '?',
                apiCall: () => maintenanceTaskApi.execute(id, { execution_result: '', actual_hours: 0 }),
                visibleWhen: (s) => s === 'pending' || s === 'in_progress',
            },
            {
                key: 'verify',
                label: t('assets.lifecycle.maintenanceTask.actions.verify'),
                type: 'success',
                confirmMessage: t('assets.lifecycle.maintenanceTask.actions.verify') + '?',
                apiCall: () => maintenanceTaskApi.verify(id, 'approved'),
                visibleWhen: (s) => s === 'completed',
            },
            {
                key: 'skip',
                label: t('assets.lifecycle.maintenanceTask.actions.skip'),
                type: 'default',
                confirmMessage: t('assets.lifecycle.maintenanceTask.actions.skip') + '?',
                confirmType: 'warning',
                apiCall: () => maintenanceTaskApi.skip(id, ''),
                visibleWhen: (s) => s === 'pending',
            },
        ],
    },

    DisposalRequest: {
        fetchDetail: (id) => disposalRequestApi.detail(id),
        refreshDetail: (id) => disposalRequestApi.detail(id),
        workflowSteps: {
            steps: ['draft', 'submitted', 'appraising', 'approved', 'completed'],
            i18nPrefix: 'assets.lifecycle.disposalRequest.status'
        },
        statusActions: (id, t) => [
            {
                key: 'submit',
                label: t('assets.lifecycle.disposalRequest.actions.submit'),
                type: 'primary',
                confirmMessage: t('assets.lifecycle.disposalRequest.actions.submit') + '?',
                apiCall: () => disposalRequestApi.submit(id),
                visibleWhen: (s) => s === 'draft',
            },
            {
                key: 'startAppraisal',
                label: t('assets.lifecycle.disposalRequest.actions.startAppraisal'),
                type: 'primary',
                confirmMessage: t('assets.lifecycle.disposalRequest.actions.startAppraisal') + '?',
                apiCall: () => disposalRequestApi.startAppraisal(id),
                visibleWhen: (s) => s === 'submitted',
            },
            {
                key: 'approve',
                label: t('assets.lifecycle.disposalRequest.actions.approve'),
                type: 'success',
                confirmMessage: t('assets.lifecycle.disposalRequest.actions.approve') + '?',
                apiCall: () => disposalRequestApi.approve(id, 'approved'),
                visibleWhen: (s) => s === 'appraising',
            },
            {
                key: 'reject',
                label: t('assets.lifecycle.disposalRequest.actions.reject'),
                type: 'danger',
                confirmMessage: t('assets.lifecycle.disposalRequest.actions.reject') + '?',
                confirmType: 'warning',
                apiCall: () => disposalRequestApi.approve(id, 'rejected'),
                visibleWhen: (s) => s === 'appraising',
            },
            {
                key: 'cancel',
                label: t('common.actions.cancel'),
                type: 'default',
                confirmMessage: t('common.messages.confirmCancel'),
                confirmType: 'warning',
                apiCall: () => disposalRequestApi.cancel(id),
                visibleWhen: (s) => ['draft', 'submitted'].includes(s),
            },
        ],
        subTable: {
            columns: (t) => [
                { prop: 'assetDisplay', label: t('assets.lifecycle.disposalRequest.form.assetLabel') },
                { prop: 'assetCode', label: t('assets.lifecycle.disposalRequest.form.assetCode'), width: 140 },
                { prop: 'disposalMethod', label: t('assets.lifecycle.disposalRequest.form.disposalMethod'), width: 140 },
                { prop: 'appraisalValue', label: t('assets.lifecycle.disposalRequest.form.appraisalValue'), width: 130, align: 'right' },
                { prop: 'actualDisposalValue', label: t('assets.lifecycle.disposalRequest.form.disposalValue'), width: 130, align: 'right' },
            ],
            fetchItems: (id) => disposalRequestApi.items(id).then((r: any) => r?.results || r || []),
        },
    },
}

/**
 * Check if a given objectCode has lifecycle extensions
 */
export function hasLifecycleExtension(objectCode: string): boolean {
    return !!lifecycleExtensionRegistry[objectCode]
}

/**
 * Get lifecycle extension for a given objectCode
 */
export function getLifecycleExtension(objectCode: string): LifecycleDetailExtension | null {
    return lifecycleExtensionRegistry[objectCode] || null
}
