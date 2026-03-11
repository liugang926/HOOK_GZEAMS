import { computed, ref, type ComputedRef, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { Router } from 'vue-router'
import { createObjectClient, type ObjectMetadata } from '@/api/dynamic'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'

interface Params {
  objectCode: Ref<string>
  recordId: Ref<string>
  isEdit: ComputedRef<boolean>
  router: Router
  shouldLoadRecord: () => boolean
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
  permissions: {
    view: true,
    add: true,
    change: true,
    delete: true,
  },
} as ObjectMetadata)

export const useDynamicFormController = ({
  objectCode,
  recordId,
  isEdit,
  router,
  shouldLoadRecord,
  t,
}: Params) => {
  const objectMetadata = ref<ObjectMetadata | null>(null)
  const metadataPermissions = ref<ObjectMetadata['permissions'] | null>(null)
  const runtimePermissions = ref<RuntimePermissions | null>(null)
  const loading = ref(false)
  const loadError = ref<string | null>(null)
  const submitting = ref(false)
  const formData = ref<Record<string, any>>({})
  const dynamicFormRef = ref<any>(null)

  const apiClient = computed(() => createObjectClient(objectCode.value))

  const handleModelUpdate = (data: Record<string, any>) => {
    formData.value = data
  }

  const handleCancel = () => {
    router.push(`/objects/${objectCode.value}`)
  }

  const handleSubmit = async () => {
    submitting.value = true
    try {
      const valid = await dynamicFormRef.value?.validate?.()
      if (valid === false) {
        submitting.value = false
        return
      }

      const payload = dynamicFormRef.value?.getSubmitData?.() || formData.value

      if (isEdit.value) {
        await apiClient.value.update(recordId.value, payload)
        ElMessage.success(t('common.messages.updateSuccess'))
      } else {
        await apiClient.value.create(payload)
        ElMessage.success(t('common.messages.createSuccess'))
      }

      router.push(`/objects/${objectCode.value}`)
    } catch (error: any) {
      ElMessage.error(error.message || t('common.messages.operationFailed'))
    } finally {
      submitting.value = false
    }
  }

  const loadData = async () => {
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
        objectMetadata.value = metadata
        metadataPermissions.value = metadata.permissions || null
      } else {
        const fallback = buildFallbackMetadata(objectCode.value)
        objectMetadata.value = fallback
        metadataPermissions.value = fallback.permissions
        console.warn('[DynamicFormPage] Metadata load failed, runtime permissions remain active')
      }

      if (runtimeResult.status === 'rejected' && metadataResult.status === 'rejected') {
        const runtimeError = runtimeResult.reason instanceof Error ? runtimeResult.reason.message : ''
        const metadataError = metadataResult.reason instanceof Error ? metadataResult.reason.message : ''
        loadError.value = metadataError || runtimeError || t('system.businessObject.messages.loadMetadataFailed')
        return
      }

      if (isEdit.value && shouldLoadRecord()) {
        const recordResponse = await apiClient.value.get(recordId.value)
        formData.value = recordResponse || {}
      }
    } catch (error: any) {
      loadError.value = error.message || t('common.messages.operationFailed')
      if (!error?.isHandled) ElMessage.error(loadError.value || t('common.messages.operationFailed'))
    } finally {
      loading.value = false
    }
  }

  const retryLoad = () => {
    loadData()
  }

  return {
    apiClient,
    dynamicFormRef,
    formData,
    handleCancel,
    handleModelUpdate,
    handleSubmit,
    loadData,
    loadError,
    loading,
    metadataPermissions,
    objectMetadata,
    retryLoad,
    runtimePermissions,
    submitting,
  }
}
