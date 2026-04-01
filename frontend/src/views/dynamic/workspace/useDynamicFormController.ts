import { computed, ref, type ComputedRef, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { Router } from 'vue-router'
import { createObjectClient, type ObjectMetadata } from '@/api/dynamic'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'
import type { AggregateDocumentResponse, RuntimeAggregate, RuntimeWorkbench } from '@/types/runtime'
import {
  buildAggregateDocumentFormData,
  buildAggregateDocumentPayload,
  resolveAggregateDocumentDetailPath,
  supportsAggregateDocument,
} from './aggregateDocument'
import {
  extractDynamicFormRoutePrefill,
  resolveDynamicFormReturnTo,
} from './dynamicFormPrefill'

interface Params {
  objectCode: Ref<string>
  recordId: Ref<string>
  isEdit: ComputedRef<boolean>
  router: Router
  routeQuery: Ref<Record<string, any> | undefined>
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
  routeQuery,
  shouldLoadRecord,
  t,
}: Params) => {
  const objectMetadata = ref<ObjectMetadata | null>(null)
  const metadataPermissions = ref<ObjectMetadata['permissions'] | null>(null)
  const runtimePermissions = ref<RuntimePermissions | null>(null)
  const runtimeAggregate = ref<RuntimeAggregate | null>(null)
  const runtimeWorkbench = ref<RuntimeWorkbench | null>(null)
  const documentPayload = ref<AggregateDocumentResponse | null>(null)
  const loading = ref(false)
  const loadError = ref<string | null>(null)
  const submitting = ref(false)
  const formData = ref<Record<string, any>>({})
  const dynamicFormRef = ref<any>(null)

  const apiClient = computed(() => createObjectClient(objectCode.value))
  const routePrefill = computed(() => extractDynamicFormRoutePrefill(routeQuery.value))
  const returnTo = computed(() => resolveDynamicFormReturnTo(routeQuery.value))
  const usesAggregateDocument = computed(() => supportsAggregateDocument(objectCode.value, runtimeAggregate.value))

  const handleModelUpdate = (data: Record<string, any>) => {
    formData.value = data
  }

  const handleCancel = () => {
    if (isEdit.value && usesAggregateDocument.value) {
      const detailPath = resolveAggregateDocumentDetailPath(objectCode.value, documentPayload.value)
      if (detailPath) {
        router.push(detailPath)
        return
      }
    }
    router.push(returnTo.value || `/objects/${objectCode.value}`)
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

      if (usesAggregateDocument.value) {
        const documentRequest = buildAggregateDocumentPayload(payload, runtimeAggregate.value)
        if (isEdit.value) {
          documentPayload.value = await apiClient.value.updateDocument(recordId.value, documentRequest, 'edit')
        } else {
          documentPayload.value = await apiClient.value.createDocument(documentRequest, 'edit')
        }
      } else if (isEdit.value) {
        await apiClient.value.update(recordId.value, payload)
        ElMessage.success(t('common.messages.updateSuccess'))
      } else {
        await apiClient.value.create(payload)
      }

      if (usesAggregateDocument.value) {
        formData.value = documentPayload.value ? buildAggregateDocumentFormData(documentPayload.value) : formData.value
        ElMessage.success(t(isEdit.value ? 'common.messages.updateSuccess' : 'common.messages.createSuccess'))
      } else if (!isEdit.value) {
        ElMessage.success(t('common.messages.createSuccess'))
      }

      if (usesAggregateDocument.value) {
        const detailPath = resolveAggregateDocumentDetailPath(objectCode.value, documentPayload.value)
        if (detailPath && !returnTo.value) {
          router.push(detailPath)
          return
        }
      }

      router.push(returnTo.value || `/objects/${objectCode.value}`)
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
        resolveRuntimeLayout(objectCode.value, 'edit', { includeRelations: true }),
        apiClient.value.getMetadata(),
      ])

      runtimePermissions.value = runtimeResult.status === 'fulfilled'
        ? (runtimeResult.value.permissions || null)
        : null
      runtimeAggregate.value = runtimeResult.status === 'fulfilled'
        ? (runtimeResult.value.aggregate || null)
        : null
      runtimeWorkbench.value = runtimeResult.status === 'fulfilled'
        ? (runtimeResult.value.workbench || null)
        : null
      documentPayload.value = null

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
        if (usesAggregateDocument.value) {
          documentPayload.value = await apiClient.value.getDocument(recordId.value, 'edit')
          formData.value = buildAggregateDocumentFormData(documentPayload.value)
        } else {
          const recordResponse = await apiClient.value.get(recordId.value)
          formData.value = recordResponse || {}
        }
      } else if (!isEdit.value) {
        formData.value = { ...routePrefill.value }
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
    documentPayload,
    runtimeAggregate,
    runtimeWorkbench,
    runtimePermissions,
    submitting,
    usesAggregateDocument,
  }
}
