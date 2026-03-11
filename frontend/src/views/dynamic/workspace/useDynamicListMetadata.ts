import { ref, type ComputedRef, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { ObjectMetadata } from '@/types'
import { extractRuntimeListColumns } from '@/adapters/runtimeListLayoutAdapter'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'

interface Params {
  objectCode: Ref<string>
  apiClient: ComputedRef<any>
  t: (key: string) => string
}

const createFallbackMetadata = (objectCode: string): ObjectMetadata => ({
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

const withTimeout = async <T>(promise: Promise<T>, timeoutMs: number, timeoutMessage: string): Promise<T> => {
  let timer: ReturnType<typeof setTimeout> | null = null
  try {
    return await Promise.race([
      promise,
      new Promise<T>((_, reject) => {
        timer = setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs)
      }),
    ])
  } finally {
    if (timer) clearTimeout(timer)
  }
}

export const useDynamicListMetadata = ({
  objectCode,
  apiClient,
  t,
}: Params) => {
  const objectMetadata = ref<ObjectMetadata | null>(null)
  const runtimeFields = ref<any[]>([])
  const runtimeColumns = ref<any[]>([])
  const runtimeLayoutConfig = ref<Record<string, any> | null>(null)
  const runtimePermissions = ref<RuntimePermissions | null>(null)
  const loading = ref(false)
  const loadError = ref<string | null>(null)

  const loadMetadata = async () => {
    loading.value = true
    loadError.value = null
    runtimeFields.value = []
    runtimeColumns.value = []
    runtimeLayoutConfig.value = null
    runtimePermissions.value = null

    try {
      const [runtimeResult, metadataResult] = await Promise.allSettled([
        withTimeout(
          resolveRuntimeLayout(objectCode.value, 'list', { includeRelations: false }),
          2500,
          t('common.messages.requestTimeout')
        ),
        apiClient.value.getMetadata(),
      ])

      if (runtimeResult.status === 'fulfilled') {
        const resolved = runtimeResult.value
        runtimeFields.value = Array.isArray(resolved.fields)
          ? resolved.fields
          : (Array.isArray(resolved.editableFields) ? resolved.editableFields : [])
        runtimeColumns.value = extractRuntimeListColumns({
          layout: {
            layoutConfig: resolved.layoutConfig,
          },
        })
        runtimeLayoutConfig.value = resolved.layoutConfig || null
        runtimePermissions.value = resolved.permissions
      }

      if (metadataResult.status === 'fulfilled') {
        const metadataPayload = ((metadataResult.value as any)?.data ?? metadataResult.value) as ObjectMetadata
        objectMetadata.value = metadataPayload || createFallbackMetadata(objectCode.value)
      } else {
        objectMetadata.value = createFallbackMetadata(objectCode.value)
      }

      if (runtimeResult.status === 'rejected') {
        if (metadataResult.status === 'fulfilled') {
          const fallbackFields = objectMetadata.value?.fields || []
          runtimeFields.value = Array.isArray(fallbackFields) ? fallbackFields : []
          const fallbackLayout = (objectMetadata.value as any)?.layouts?.list || null
          runtimeLayoutConfig.value = fallbackLayout && typeof fallbackLayout === 'object' ? fallbackLayout : null
          runtimeColumns.value = (fallbackLayout as any)?.columns || []
        } else {
          throw runtimeResult.reason
        }
      }
    } catch (error: any) {
      loadError.value = error.message || t('system.businessObject.messages.loadMetadataFailed')
      ElMessage.error(loadError.value || t('system.businessObject.messages.loadMetadataFailed'))
    } finally {
      loading.value = false
    }
  }

  const retryLoad = () => {
    loadMetadata()
  }

  return {
    loadError,
    loadMetadata,
    loading,
    objectMetadata,
    retryLoad,
    runtimeColumns,
    runtimeFields,
    runtimeLayoutConfig,
    runtimePermissions,
  }
}
