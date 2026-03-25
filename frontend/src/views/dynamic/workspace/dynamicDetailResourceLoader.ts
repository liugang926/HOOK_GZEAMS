import type { ObjectMetadata } from '@/api/dynamic'
import type {
  RuntimeLayoutResolution,
  RuntimePermissions,
} from '@/platform/layout/runtimeLayoutResolver'
import type { AggregateDocumentResponse, RuntimeAggregate, RuntimeWorkbench } from '@/types/runtime'
import {
  buildAggregateDocumentFormData,
  supportsAggregateDocument,
} from './aggregateDocument'

export interface DynamicDetailResourceLoadResult {
  metadataPermissions: ObjectMetadata['permissions'] | null
  objectMetadata: ObjectMetadata | null
  runtimePermissions: RuntimePermissions | null
  runtimeAggregate: RuntimeAggregate | null
  runtimeWorkbench: RuntimeWorkbench | null
  documentPayload: AggregateDocumentResponse | null
  loadedRecord: Record<string, any> | null
  lifecycleRecordData: Record<string, any> | null
  loadError: string | null
  usesAggregateDocument: boolean
  usedFallbackMetadata: boolean
}

interface LoadDynamicDetailResourcesParams {
  objectCode: string
  recordId: string
  t: (key: string) => string
  loadRuntimeLayout: () => Promise<RuntimeLayoutResolution>
  loadMetadata: () => Promise<ObjectMetadata | null | undefined>
  loadDocument: (recordId: string) => Promise<AggregateDocumentResponse>
}

export const buildDynamicDetailFallbackMetadata = (objectCode: string): ObjectMetadata => ({
  code: objectCode,
  name: objectCode,
  isHardcoded: true,
  enableWorkflow: false,
  enableVersion: false,
  enableSoftDelete: true,
  fields: [],
  layouts: {},
  permissions: { view: true, add: true, change: true, delete: true },
} as ObjectMetadata)

export const resolveDynamicDetailLoadError = ({
  runtimeError,
  metadataError,
  documentError,
  t,
}: {
  runtimeError?: unknown
  metadataError?: unknown
  documentError?: unknown
  t: (key: string) => string
}) => {
  const resolveMessage = (value: unknown) => {
    return value instanceof Error ? value.message : ''
  }

  return (
    resolveMessage(documentError) ||
    resolveMessage(metadataError) ||
    resolveMessage(runtimeError) ||
    t('system.businessObject.messages.loadMetadataFailed')
  )
}

export const loadDynamicDetailResources = async ({
  objectCode,
  recordId,
  t,
  loadRuntimeLayout,
  loadMetadata,
  loadDocument,
}: LoadDynamicDetailResourcesParams): Promise<DynamicDetailResourceLoadResult> => {
  const [runtimeResult, metadataResult] = await Promise.allSettled([
    loadRuntimeLayout(),
    loadMetadata(),
  ])

  const runtimePermissions = runtimeResult.status === 'fulfilled'
    ? (runtimeResult.value.permissions || null)
    : null
  const runtimeAggregate = runtimeResult.status === 'fulfilled'
    ? (runtimeResult.value.aggregate || null)
    : null
  const runtimeWorkbench = runtimeResult.status === 'fulfilled'
    ? (runtimeResult.value.workbench || null)
    : null

  const metadataValue = metadataResult.status === 'fulfilled'
    ? (metadataResult.value || null)
    : null
  const usedFallbackMetadata = !metadataValue
  const objectMetadata = metadataValue || buildDynamicDetailFallbackMetadata(objectCode)
  const metadataPermissions = objectMetadata.permissions || null

  let loadError: string | null = null
  if (runtimeResult.status === 'rejected' && metadataResult.status === 'rejected') {
    loadError = resolveDynamicDetailLoadError({
      runtimeError: runtimeResult.reason,
      metadataError: metadataResult.reason,
      t,
    })
  }

  const usesAggregateDocument = supportsAggregateDocument(objectCode, runtimeAggregate)
  let documentPayload: AggregateDocumentResponse | null = null
  let loadedRecord: Record<string, any> | null = null
  let lifecycleRecordData: Record<string, any> | null = null

  if (!loadError && recordId && usesAggregateDocument) {
    try {
      documentPayload = await loadDocument(recordId)
      const normalizedRecord = buildAggregateDocumentFormData(documentPayload)
      loadedRecord = normalizedRecord
      lifecycleRecordData = normalizedRecord
    } catch (error) {
      loadError = resolveDynamicDetailLoadError({
        documentError: error,
        t,
      })
    }
  }

  return {
    metadataPermissions,
    objectMetadata,
    runtimePermissions,
    runtimeAggregate,
    runtimeWorkbench,
    documentPayload,
    loadedRecord,
    lifecycleRecordData,
    loadError,
    usesAggregateDocument,
    usedFallbackMetadata,
  }
}
