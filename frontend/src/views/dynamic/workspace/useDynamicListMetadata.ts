import { ref, type ComputedRef, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { ObjectMetadata } from '@/types'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'
import { loadDynamicListResources } from './dynamicListResourceLoader'

interface Params {
  objectCode: Ref<string>
  apiClient: ComputedRef<any>
  t: (key: string) => string
}

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
      const result = await loadDynamicListResources({
        objectCode: objectCode.value,
        t,
        loadRuntimeLayout: () => withTimeout(
          resolveRuntimeLayout(objectCode.value, 'list', { includeRelations: false }),
          2500,
          t('common.messages.requestTimeout')
        ),
        loadMetadata: async () => {
          const metadataResult = await apiClient.value.getMetadata()
          return ((metadataResult as any)?.data ?? metadataResult) as ObjectMetadata
        },
      })

      objectMetadata.value = result.objectMetadata
      runtimeFields.value = result.runtimeFields
      runtimeColumns.value = result.runtimeColumns
      runtimeLayoutConfig.value = result.runtimeLayoutConfig
      runtimePermissions.value = result.runtimePermissions
      loadError.value = result.loadError

      if (loadError.value) {
        ElMessage.error(loadError.value || t('system.businessObject.messages.loadMetadataFailed'))
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
