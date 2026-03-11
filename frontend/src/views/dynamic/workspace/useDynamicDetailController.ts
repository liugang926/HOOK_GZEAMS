import { computed, ref, type Ref } from 'vue'
import type { Router } from 'vue-router'
import { createObjectClient, type ObjectMetadata } from '@/api/dynamic'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'
import { deriveObjectCodeFromRelationCode } from '@/platform/reference/relationObjectCode'

interface Params {
  objectCode: Ref<string>
  recordId: Ref<string>
  router: Router
  t: (key: string) => string
}

const buildFallbackMetadata = (objectCode: string): ObjectMetadata => ({
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

export const useDynamicDetailController = ({
  objectCode,
  recordId,
  router,
  t,
}: Params) => {
  const metadataPermissions = ref<ObjectMetadata['permissions'] | null>(null)
  const objectMetadata = ref<ObjectMetadata | null>(null)
  const runtimePermissions = ref<RuntimePermissions | null>(null)
  const loading = ref(false)
  const loadError = ref<string | null>(null)
  const detailPageRef = ref<any>(null)
  const lifecycleRecordData = ref<Record<string, any> | null>(null)
  const loadedRecord = ref<Record<string, any> | null>(null)

  const apiClient = computed(() => createObjectClient(objectCode.value))

  const handleRecordLoaded = (record: any) => {
    loadedRecord.value = record || null
    lifecycleRecordData.value = record || null
  }

  const handleLifecycleRefresh = async () => {
    if (detailPageRef.value?.refresh) {
      await detailPageRef.value.refresh()
    }
  }

  const loadMetadata = async () => {
    loading.value = true
    loadError.value = null
    try {
      const [runtimeResult, metadataResult] = await Promise.allSettled([
        resolveRuntimeLayout(objectCode.value, 'edit', { includeRelations: false }),
        apiClient.value.getMetadata(),
      ])

      runtimePermissions.value = runtimeResult.status === 'fulfilled'
        ? (runtimeResult.value.permissions || null)
        : null

      if (metadataResult.status === 'fulfilled') {
        const metadata = (metadataResult.value as ObjectMetadata) || buildFallbackMetadata(objectCode.value)
        metadataPermissions.value = metadata.permissions || null
        objectMetadata.value = metadata
      } else {
        const fallback = buildFallbackMetadata(objectCode.value)
        metadataPermissions.value = fallback.permissions
        objectMetadata.value = fallback
        console.warn('[DynamicDetailPage] Metadata load failed, runtime permissions remain active')
      }

      if (runtimeResult.status === 'rejected' && metadataResult.status === 'rejected') {
        const runtimeError = runtimeResult.reason instanceof Error ? runtimeResult.reason.message : ''
        const metadataError = metadataResult.reason instanceof Error ? metadataResult.reason.message : ''
        loadError.value = metadataError || runtimeError || t('system.businessObject.messages.loadMetadataFailed')
      }
    } finally {
      loading.value = false
    }
  }

  const retryLoad = () => {
    loadMetadata()
  }

  const resolveRelationObjectCode = (relationCode: string, targetObjectCode?: string): string => {
    const explicitTarget = String(targetObjectCode || '').trim()
    if (explicitTarget) return explicitTarget
    return deriveObjectCodeFromRelationCode(relationCode)
  }

  const handleRelatedRecordClick = (relationCode: string, record: any, targetObjectCode?: string): void => {
    const relatedCode = resolveRelationObjectCode(relationCode, targetObjectCode)
    if (!relatedCode || !record?.id) return
    router.push(`/objects/${encodeURIComponent(relatedCode)}/${encodeURIComponent(String(record.id))}`)
  }

  const handleRelatedRecordEdit = (relationCode: string, record: any, targetObjectCode?: string): void => {
    const relatedCode = resolveRelationObjectCode(relationCode, targetObjectCode)
    if (!relatedCode || !record?.id) return
    router.push(`/objects/${encodeURIComponent(relatedCode)}/${encodeURIComponent(String(record.id))}/edit`)
  }

  const handleBackToList = () => {
    router.push(`/objects/${encodeURIComponent(objectCode.value)}`)
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
    runtimePermissions,
  }
}
