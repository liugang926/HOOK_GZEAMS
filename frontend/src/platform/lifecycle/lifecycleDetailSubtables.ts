import {
  assetReceiptActionApi,
  disposalRequestActionApi,
  purchaseRequestActionApi
} from '@/api/lifecycleActionApi'

import type { SubTableConfig } from './lifecycleDetailTypes'

const unwrapLifecycleItems = async (request: Promise<any>): Promise<any[]> => {
  const response = await request
  return response?.results || response || []
}

export const lifecycleSubTableRegistry: Partial<Record<string, SubTableConfig>> = {
  PurchaseRequest: {
    columns: (t) => [
      { prop: 'itemName', label: t('assets.lifecycle.purchaseRequest.form.assetName') },
      { prop: 'specification', label: t('assets.lifecycle.purchaseRequest.form.specification'), width: 160 },
      { prop: 'quantity', label: t('assets.lifecycle.purchaseRequest.form.quantity'), width: 100, align: 'right' },
      { prop: 'unitPrice', label: t('assets.lifecycle.purchaseRequest.form.estimatedUnitPrice'), width: 130, align: 'right' },
      { prop: 'totalAmount', label: t('assets.lifecycle.purchaseRequest.columns.totalAmount'), width: 130, align: 'right' },
      { prop: 'suggestedSupplier', label: t('assets.lifecycle.purchaseRequest.form.supplier'), width: 140 },
      { prop: 'remark', label: t('assets.lifecycle.purchaseRequest.form.remark') },
    ],
    fetchItems: (id) => unwrapLifecycleItems(purchaseRequestActionApi.items(id)),
    summaryMethod: ({ columns, data }) =>
      columns.map((column: any, index: number) => {
        if (index === 0) return ''
        if (column.property === 'totalAmount') {
          const sum = data.reduce((acc, row) => acc + (Number(row.totalAmount) || 0), 0)
          return `楼 ${sum.toFixed(2)}`
        }
        if (column.property === 'quantity') {
          return data.reduce((acc, row) => acc + (Number(row.quantity) || 0), 0)
        }
        return ''
      }),
  },
  AssetReceipt: {
    columns: (t) => [
      { prop: 'assetDisplay', label: t('assets.lifecycle.assetReceipt.form.assetName') },
      { prop: 'quantity', label: t('assets.lifecycle.purchaseRequest.form.quantity'), width: 100, align: 'right' },
      { prop: 'inspectionResult', label: t('assets.lifecycle.assetReceipt.form.inspectionResult'), width: 140 },
    ],
    fetchItems: (id) => unwrapLifecycleItems(assetReceiptActionApi.items(id)),
  },
  DisposalRequest: {
    columns: (t) => [
      { prop: 'assetDisplay', label: t('assets.lifecycle.disposalRequest.form.assetLabel') },
      { prop: 'assetCode', label: t('assets.lifecycle.disposalRequest.form.assetCode'), width: 140 },
      { prop: 'disposalMethod', label: t('assets.lifecycle.disposalRequest.form.disposalMethod'), width: 140 },
      { prop: 'appraisalValue', label: t('assets.lifecycle.disposalRequest.form.appraisalValue'), width: 130, align: 'right' },
      { prop: 'actualDisposalValue', label: t('assets.lifecycle.disposalRequest.form.disposalValue'), width: 130, align: 'right' },
    ],
    fetchItems: (id) => unwrapLifecycleItems(disposalRequestActionApi.items(id)),
  },
}
