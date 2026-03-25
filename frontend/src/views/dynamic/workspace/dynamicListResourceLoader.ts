import type { ObjectMetadata } from '@/types'
import { extractRuntimeListColumns } from '@/adapters/runtimeListLayoutAdapter'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'

export interface DynamicListResourceLoadResult {
  objectMetadata: ObjectMetadata
  runtimeFields: any[]
  runtimeColumns: any[]
  runtimeLayoutConfig: Record<string, any> | null
  runtimePermissions: RuntimePermissions | null
  loadError: string | null
  usedFallbackMetadata: boolean
}

interface LoadDynamicListResourcesParams {
  objectCode: string
  t: (key: string) => string
  loadRuntimeLayout: () => Promise<{
    fields?: any[]
    editableFields?: any[]
    layoutConfig?: Record<string, any> | null
    permissions?: RuntimePermissions | null
  }>
  loadMetadata: () => Promise<ObjectMetadata | null | undefined>
}

export const buildDynamicListFallbackMetadata = (objectCode: string): ObjectMetadata => ({
  code: objectCode,
  name: objectCode,
  isHardcoded: true,
  enableWorkflow: false,
  enableVersion: false,
  enableSoftDelete: true,
  fields: [],
  layouts: {},
  permissions: {
    view: true,
    add: true,
    change: true,
    delete: true,
  },
} as ObjectMetadata)

export const resolveDynamicListLoadError = ({
  runtimeError,
  metadataError,
  t,
}: {
  runtimeError?: unknown
  metadataError?: unknown
  t: (key: string) => string
}) => {
  const resolveMessage = (value: unknown) => value instanceof Error ? value.message : ''

  return (
    resolveMessage(runtimeError) ||
    resolveMessage(metadataError) ||
    t('system.businessObject.messages.loadMetadataFailed')
  )
}

export const loadDynamicListResources = async ({
  objectCode,
  t,
  loadRuntimeLayout,
  loadMetadata,
}: LoadDynamicListResourcesParams): Promise<DynamicListResourceLoadResult> => {
  const [runtimeResult, metadataResult] = await Promise.allSettled([
    loadRuntimeLayout(),
    loadMetadata(),
  ])

  const metadataValue = metadataResult.status === 'fulfilled'
    ? (metadataResult.value || null)
    : null
  const usedFallbackMetadata = !metadataValue
  const objectMetadata = metadataValue || buildDynamicListFallbackMetadata(objectCode)

  let runtimeFields: any[] = []
  let runtimeColumns: any[] = []
  let runtimeLayoutConfig: Record<string, any> | null = null
  let runtimePermissions: RuntimePermissions | null = null
  let loadError: string | null = null

  if (runtimeResult.status === 'fulfilled') {
    runtimeFields = Array.isArray(runtimeResult.value.fields)
      ? runtimeResult.value.fields
      : (Array.isArray(runtimeResult.value.editableFields) ? runtimeResult.value.editableFields : [])
    runtimeColumns = extractRuntimeListColumns({
      layout: {
        layoutConfig: runtimeResult.value.layoutConfig,
      },
    })
    runtimeLayoutConfig = runtimeResult.value.layoutConfig || null
    runtimePermissions = runtimeResult.value.permissions || null
  }

  if (runtimeResult.status === 'rejected') {
    if (metadataResult.status === 'fulfilled') {
      const fallbackFields = objectMetadata.fields || []
      runtimeFields = Array.isArray(fallbackFields) ? fallbackFields : []
      const fallbackLayout = (objectMetadata as any)?.layouts?.list || null
      runtimeLayoutConfig = fallbackLayout && typeof fallbackLayout === 'object' ? fallbackLayout : null
      runtimeColumns = (fallbackLayout as any)?.columns || []
    } else {
      loadError = resolveDynamicListLoadError({
        runtimeError: runtimeResult.reason,
        metadataError: metadataResult.reason,
        t,
      })
    }
  }

  return {
    objectMetadata,
    runtimeFields,
    runtimeColumns,
    runtimeLayoutConfig,
    runtimePermissions,
    loadError,
    usedFallbackMetadata,
  }
}
