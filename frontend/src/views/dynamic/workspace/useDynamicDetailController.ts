import { computed, ref, type Ref } from 'vue'
import type { Router } from 'vue-router'
import { createObjectClient, type ObjectMetadata } from '@/api/dynamic'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'
import type {
  AggregateDocumentResponse,
  ObjectSlaSummary,
  RuntimeAggregate,
  RuntimeWorkbench,
} from '@/types/runtime'
import { supportsAggregateDocument } from './aggregateDocument'
import {
  buildDynamicObjectListPath,
  pushDynamicObjectDetail,
  pushDynamicObjectEdit,
} from './dynamicDetailNavigation'
import {
  loadDynamicDetailResources,
} from './dynamicDetailResourceLoader'

interface Params {
  objectCode: Ref<string>
  recordId: Ref<string>
  router: Router
  t: (key: string) => string
}

export const useDynamicDetailController = ({
  objectCode,
  recordId,
  router,
  t,
}: Params) => {
  const metadataPermissions = ref<ObjectMetadata['permissions'] | null>(null)
  const objectMetadata = ref<ObjectMetadata | null>(null)
  const runtimePermissions = ref<RuntimePermissions | null>(null)
  const runtimeAggregate = ref<RuntimeAggregate | null>(null)
  const runtimeWorkbench = ref<RuntimeWorkbench | null>(null)
  const objectSla = ref<ObjectSlaSummary | null>(null)
  const documentPayload = ref<AggregateDocumentResponse | null>(null)
  const loading = ref(false)
  const loadError = ref<string | null>(null)
  const detailPageRef = ref<any>(null)
  const lifecycleRecordData = ref<Record<string, any> | null>(null)
  const loadedRecord = ref<Record<string, any> | null>(null)

  const apiClient = computed(() => createObjectClient(objectCode.value))
  const usesAggregateDocument = computed(() => supportsAggregateDocument(objectCode.value, runtimeAggregate.value))

  const handleRecordLoaded = (record: any) => {
    loadedRecord.value = record || null
    lifecycleRecordData.value = record || null
  }

  const handleLifecycleRefresh = async () => {
    if (usesAggregateDocument.value) {
      await loadMetadata()
      return
    }
    if (detailPageRef.value?.refresh) {
      await detailPageRef.value.refresh()
    }
  }

  const loadMetadata = async () => {
    loading.value = true
    loadError.value = null
    try {
      const [result, slaResult] = await Promise.all([
        loadDynamicDetailResources({
          objectCode: objectCode.value,
          recordId: recordId.value,
          t,
          loadRuntimeLayout: () => resolveRuntimeLayout(objectCode.value, 'edit', { includeRelations: true }),
          loadMetadata: () => apiClient.value.getMetadata(),
          loadDocument: (targetRecordId) => apiClient.value.getDocument(targetRecordId, 'readonly'),
        }),
        apiClient.value.getSla(recordId.value).catch(() => null),
      ])

      metadataPermissions.value = result.metadataPermissions
      objectMetadata.value = result.objectMetadata as ObjectMetadata | null
      runtimePermissions.value = result.runtimePermissions
      runtimeAggregate.value = result.runtimeAggregate
      runtimeWorkbench.value = result.runtimeWorkbench
      objectSla.value = slaResult
      documentPayload.value = result.documentPayload
      loadError.value = result.loadError

      if (result.usedFallbackMetadata && !result.loadError) {
        console.warn('[DynamicDetailPage] Metadata load failed, runtime permissions remain active')
      }

      if (result.usesAggregateDocument) {
        loadedRecord.value = result.loadedRecord
        lifecycleRecordData.value = result.lifecycleRecordData
      } else {
        loadedRecord.value = null
        lifecycleRecordData.value = null
      }
    } finally {
      loading.value = false
    }
  }

  const retryLoad = () => {
    loadMetadata()
  }

  const handleRelatedRecordClick = (relationCode: string, record: any, targetObjectCode?: string): void => {
    pushDynamicObjectDetail({
      router,
      relationCode,
      record,
      targetObjectCode,
    })
  }

  const handleRelatedRecordEdit = (relationCode: string, record: any, targetObjectCode?: string): void => {
    pushDynamicObjectEdit({
      router,
      relationCode,
      record,
      targetObjectCode,
    })
  }

  const handleBackToList = () => {
    const path = buildDynamicObjectListPath(objectCode.value)
    if (!path) return
    router.push(path)
  }

  return {
    detailPageRef,
    handleBackToList,
    handleLifecycleRefresh,
    handleRecordLoaded,
    handleRelatedRecordClick,
    handleRelatedRecordEdit,
    lifecycleRecordData,
    loadError,
    loadedRecord,
    loading,
    loadMetadata,
    metadataPermissions,
    objectMetadata,
    retryLoad,
    documentPayload,
    runtimeAggregate,
    runtimeWorkbench,
    objectSla,
    runtimePermissions,
    usesAggregateDocument,
  }
}
