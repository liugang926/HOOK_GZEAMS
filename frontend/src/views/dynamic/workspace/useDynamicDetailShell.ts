import { computed, type Ref } from 'vue'
import type { ObjectMetadata } from '@/api/dynamic'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'
import type { AggregateDocumentResponse } from '@/types/runtime'
import { getLifecycleExtension, hasLifecycleExtension } from '@/platform/lifecycle/lifecycleDetailExtensions'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'
import { buildAggregateDocumentStatusActions } from '@/views/dynamic/workspace/aggregateDocumentStatusActions'
import type {
  DynamicDetailNavigationSection,
  DynamicDetailTimelineConfig,
} from './detailNavigationModel'
import {
  resolveDynamicDetailEffectivePermissions,
  shouldShowDynamicDetailEnhancements,
} from './dynamicDetailPageShellModel'
import { useDynamicDetailWorkspace } from './useDynamicDetailWorkspace'

interface Params {
  objectCode: Ref<string>
  recordId: Ref<string>
  objectMetadata: Ref<ObjectMetadata | null>
  metadataPermissions: Ref<ObjectMetadata['permissions'] | null>
  runtimePermissions: Ref<RuntimePermissions | null>
  documentPayload: Ref<AggregateDocumentResponse | null>
  loadedRecord: Ref<Record<string, any> | null>
  detailNavigationSection: Ref<DynamicDetailNavigationSection | null>
  detailTimelineConfig: Ref<DynamicDetailTimelineConfig | null>
  t: (key: string, params?: Record<string, unknown>) => string
  te: (key: string) => boolean
  locale: Ref<string>
}

export const useDynamicDetailShell = ({
  objectCode,
  recordId,
  objectMetadata,
  metadataPermissions,
  runtimePermissions,
  documentPayload,
  loadedRecord,
  detailNavigationSection,
  detailTimelineConfig,
  t,
  te,
  locale,
}: Params) => {
  const isLifecycle = computed(() => hasLifecycleExtension(objectCode.value))
  const lifecycleExtension = computed(() => getLifecycleExtension(objectCode.value))
  const aggregateStatusActions = computed(() => {
    return buildAggregateDocumentStatusActions({
      objectCode: objectCode.value,
      recordId: recordId.value,
      document: documentPayload.value,
      t: (key: string) => t(key),
    })
  })

  const effectivePermissions = computed(() => resolveDynamicDetailEffectivePermissions(
    runtimePermissions.value,
    metadataPermissions.value,
  ))
  const canDelete = computed(() => effectivePermissions.value.delete)
  const canEdit = computed(() => effectivePermissions.value.change)
  const canView = computed(() => effectivePermissions.value.view !== false)
  const isZhLocale = computed(() => String(locale?.value || '').toLowerCase().startsWith('zh'))
  const objectDisplayName = computed(() => {
    return resolveObjectDisplayName(
      objectCode.value,
      objectMetadata.value?.name || objectMetadata.value?.nameEn || '',
      (key: string) => t(key),
      (key: string) => te(key),
    )
  })

  const workspace = useDynamicDetailWorkspace({
    isZhLocale,
    objectCode,
    recordId,
    objectMetadata,
    objectDisplayName,
    canEdit,
    loadedRecord,
  })

  const hasDetailEnhancements = computed(() => shouldShowDynamicDetailEnhancements({
    isLifecycle: isLifecycle.value,
    hasNavigationSection: Boolean(detailNavigationSection.value),
    hasTimelineConfig: Boolean(detailTimelineConfig.value),
  }))

  return {
    aggregateStatusActions,
    canDelete,
    canEdit,
    canView,
    effectivePermissions,
    hasDetailEnhancements,
    isLifecycle,
    isZhLocale,
    lifecycleExtension,
    objectDisplayName,
    ...workspace,
  }
}
