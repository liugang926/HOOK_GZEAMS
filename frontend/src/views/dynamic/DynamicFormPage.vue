<template>
  <div
    v-loading="loading"
    class="dynamic-form-page"
  >
    <div
      v-if="loadError"
      class="load-error"
    >
      <el-result
        icon="error"
        :title="t('common.messages.loadFailed') || 'Load Failed'"
        :sub-title="loadError"
      >
        <template #extra>
          <el-button
            type="primary"
            @click="retryLoad"
          >
            {{ t('common.actions.refresh') }}
          </el-button>
          <el-button @click="$router.back()">
            {{ t('common.actions.back') }}
          </el-button>
        </template>
      </el-result>
    </div>

    <div v-else>
      <DynamicForm
        ref="dynamicFormRef"
        :business-object="objectCode"
        layout-code="form"
        :model-value="formData"
        :readonly="!canEdit"
        :show-actions="false"
        :instance-id="recordId || null"
        @update:model-value="handleModelUpdate"
      />

      <div class="form-actions">
        <el-button
          v-if="canEdit"
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ t('common.actions.save') }}
        </el-button>
        <el-button
          :disabled="submitting"
          @click="handleCancel"
        >
          {{ t('common.actions.cancel') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import DynamicForm from '@/components/engine/DynamicForm.vue'
import { createObjectClient, type ObjectMetadata } from '@/api/dynamic'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const objectCode = ref<string>((route.params.code as string) || '')
const recordId = ref<string>((route.params.id as string) || '')
const metadataPermissions = ref<ObjectMetadata['permissions'] | null>(null)
const runtimePermissions = ref<RuntimePermissions | null>(null)
const loading = ref(false)
const loadError = ref<string | null>(null)
const submitting = ref(false)

const apiClient = computed(() => createObjectClient(objectCode.value))
const formData = ref<Record<string, any>>({})
const dynamicFormRef = ref<any>(null)

const isEdit = computed(() => !!recordId.value)
const effectivePermissions = computed<RuntimePermissions>(() => {
  return runtimePermissions.value || metadataPermissions.value || {
    view: true,
    add: true,
    change: true,
    delete: true
  }
})

const canEdit = computed(() => {
  return isEdit.value
    ? effectivePermissions.value.change
    : effectivePermissions.value.add
})

const buildFallbackMetadata = (): ObjectMetadata => ({
  code: objectCode.value,
  name: objectCode.value,
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
    delete: true
  }
} as ObjectMetadata)

const handleModelUpdate = (data: Record<string, any>) => {
  formData.value = data
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
      ElMessage.success(t('common.messages.updateSuccess') || 'Update Success')
    } else {
      await apiClient.value.create(payload)
      ElMessage.success(t('common.messages.createSuccess') || 'Create Success')
    }

    router.push(`/objects/${objectCode.value}`)
  } catch (error: any) {
    ElMessage.error(error.message || t('common.messages.operationFailed') || 'Operation Failed')
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  router.push(`/objects/${objectCode.value}`)
}

const loadData = async () => {
  loading.value = true
  loadError.value = null
  try {
    const [runtimeResult, metadataResult] = await Promise.allSettled([
      resolveRuntimeLayout(objectCode.value, 'edit', { includeRelations: false }),
      apiClient.value.getMetadata()
    ])

    runtimePermissions.value = runtimeResult.status === 'fulfilled'
      ? (runtimeResult.value.permissions || null)
      : null

    if (metadataResult.status === 'fulfilled') {
      const metadata = (metadataResult.value as ObjectMetadata) || buildFallbackMetadata()
      metadataPermissions.value = metadata.permissions || null
    } else {
      metadataPermissions.value = buildFallbackMetadata().permissions
      console.warn('[DynamicFormPage] Metadata load failed, runtime permissions remain active')
    }

    if (isEdit.value) {
      const recordResponse = await apiClient.value.get(recordId.value)
      formData.value = recordResponse || {}
    }
  } catch (error: any) {
    loadError.value = error.message || t('common.messages.operationFailed') || 'Operation Failed'
    if (!error?.isHandled) ElMessage.error(loadError.value)
  } finally {
    loading.value = false
  }
}

const retryLoad = () => {
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.dynamic-form-page {
  height: 100%;
  background-color: #f5f7fa;
}

.form-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
}
</style>
