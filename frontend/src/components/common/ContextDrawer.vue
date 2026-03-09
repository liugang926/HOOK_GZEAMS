<template>
  <!--
    ContextDrawer.vue
    A global slide-out drawer used to display dynamic forms (create/edit) or details
    without losing the user's current context (e.g. List Page or Parent Detail Page).
  -->
  <component
    v-if="visible"
    :is="displayMode === 'Compact' ? 'el-dialog' : 'el-drawer'"
    v-model="visible"
    v-focus-trap.autofocus="visible"
    :title="title"
    v-bind="displayMode === 'Compact' ? { width: size } : { size: size }"
    :destroy-on-close="true"
    :before-close="handleBeforeClose"
    :class="['context-container', displayMode === 'Compact' ? 'context-dialog' : 'context-drawer']"
  >
    <div
      v-loading="loading"
      class="context-container__content"
    >
      <el-result
        v-if="loadError"
        icon="error"
        :title="t('common.messages.loadFailed')"
        :sub-title="loadError"
      >
        <template #extra>
          <el-button @click="visible = false">
            {{ t('common.actions.close') }}
          </el-button>
        </template>
      </el-result>

      <template v-else>
        <DynamicForm
          ref="formRef"
          :business-object="objectCode"
          layout-code="form"
          :model-value="formData"
          :instance-id="recordId || null"
          :readonly="!canEdit"
          :show-actions="false"
          @update:model-value="handleModelUpdate"
          @dirty-change="handleDirtyChange"
          @request-save="handleFormRequestSave"
        />
      </template>
    </div>

    <template #footer>
      <div class="context-container__footer">
        <div class="footer-left">
          <transition name="el-fade-in">
            <div
              v-if="isDirty"
              class="dirty-indicator"
            >
              <el-icon class="is-warning">
                <Warning />
              </el-icon>
              <span>{{ t('system.messages.unsavedChanges') }}</span>
            </div>
          </transition>
        </div>
        <div class="footer-right">
          <el-button
            :disabled="submitting"
            @click="handleCancel"
          >
            {{ t('common.actions.cancel') }}
          </el-button>
          <el-button
            v-if="canEdit"
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            {{ t('common.actions.save') }}
          </el-button>
        </div>
      </div>
    </template>
  </component>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import DynamicForm from '@/components/engine/DynamicForm.vue'
import { createObjectClient, type ObjectMetadata } from '@/api/dynamic'
import { resolveRuntimeLayout, type RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'
import { useHotkey, useHotkeyContext } from '@/composables/useHotkeys'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  objectCode: { type: String, required: true },
  recordId: { type: String, default: '' },
  size: { type: [String, Number], default: '800px' },
  titleOverride: { type: String, default: '' }
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', payload: unknown): void
  (e: 'cancel'): void
}>()

const { t } = useI18n()

const visible = ref(props.modelValue)
const loading = ref(false)
const submitting = ref(false)
const loadError = ref<string | null>(null)
const formData = ref<Record<string, unknown>>({})
const formRef = ref<any>(null)
const isDirty = ref(false)

const metadataPermissions = ref<ObjectMetadata['permissions'] | null>(null)
const runtimePermissions = ref<RuntimePermissions | null>(null)
const objectMetadata = ref<ObjectMetadata | null>(null)
const displayMode = ref<'Detail' | 'Compact'>('Detail')

const isEdit = computed(() => !!props.recordId)
const apiClient = computed(() => createObjectClient(props.objectCode))

const effectivePermissions = computed<RuntimePermissions>(() => {
  return runtimePermissions.value || metadataPermissions.value || {
    view: true,
    add: true,
    change: true,
    delete: true
  }
})

const canView = computed(() => effectivePermissions.value.view !== false)
const canEdit = computed(() => (isEdit.value ? effectivePermissions.value.change : effectivePermissions.value.add) !== false)

const title = computed(() => {
  if (props.titleOverride) return props.titleOverride
  const objName = objectMetadata.value?.name || props.objectCode
  return isEdit.value
    ? `${t('common.actions.edit')} ${objName}`
    : t('common.actions.newRecord')
})

const hotkeyContextId = useHotkeyContext({
  enabled: () => visible.value
})

const handleModelUpdate = (data: Record<string, unknown>) => {
  formData.value = data
}

const handleDirtyChange = (dirty: boolean) => {
  isDirty.value = dirty
}

const handleBeforeClose = async (done: () => void) => {
  if (isDirty.value && !submitting.value) {
    try {
      await ElMessageBox.confirm(
        t('system.messages.unsavedChanges'),
        t('common.dialog.confirmTitle'),
        {
          type: 'warning',
          confirmButtonText: t('common.actions.leave'),
          cancelButtonText: t('common.actions.stay')
        }
      )
      done()
    } catch {
      // User chose to stay in drawer.
    }
    return
  }

  done()
}

const handleCancel = () => {
  handleBeforeClose(() => {
    visible.value = false
    emit('cancel')
  })
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    const valid = await formRef.value?.validate?.()
    if (valid !== true) {
      let msg = t('system.messages.validationFailed') || 'Please check for missing required fields.'
      if (valid && typeof valid === 'object') {
        msg += ` \nFields failing validation: ${Object.keys(valid).join(', ')}`
      }
      ElMessage.warning({ message: msg, duration: 8000 })
      submitting.value = false
      return
    }

    const payload = formRef.value?.getSubmitData?.() || formData.value
    let result: unknown

    if (isEdit.value) {
      result = await apiClient.value.update(props.recordId, payload)
      ElMessage.success(t('common.messages.updateSuccess'))
    } else {
      result = await apiClient.value.create(payload)
      ElMessage.success(t('common.messages.createSuccess'))
    }

    isDirty.value = false
    visible.value = false
    emit('success', result)
  } catch (error: any) {
    ElMessage.error(error?.message || t('common.messages.operationFailed'))
  } finally {
    submitting.value = false
  }
}

const handleFormRequestSave = () => {
  if (!visible.value || !canEdit.value || !isDirty.value || submitting.value || !!loadError.value) return
  void handleSubmit()
}

useHotkey('ctrl+s', () => {
  if (!visible.value || !canEdit.value || !isDirty.value || submitting.value || !!loadError.value) {
    return
  }
  void handleSubmit()
  return false
}, {
  context: hotkeyContextId,
  preventDefault: true,
  stopPropagation: true,
  allowInInputs: true,
  enabled: () => visible.value
})

const loadData = async () => {
  loading.value = true
  loadError.value = null
  isDirty.value = false
  formData.value = {}

  try {
    const [runtimeResult, metadataResult] = await Promise.allSettled([
      resolveRuntimeLayout(props.objectCode, 'edit', {
        includeRelations: false,
        preferredViewMode: isEdit.value ? undefined : 'Compact',
      }),
      apiClient.value.getMetadata()
    ])

    runtimePermissions.value = runtimeResult.status === 'fulfilled'
      ? (runtimeResult.value.permissions || null)
      : null
      
    if (runtimeResult.status === 'fulfilled') {
      displayMode.value = (runtimeResult.value.viewMode === 'Compact') ? 'Compact' : 'Detail'
    } else {
      displayMode.value = 'Detail'
    }

    if (metadataResult.status === 'fulfilled') {
      objectMetadata.value = metadataResult.value as ObjectMetadata
      metadataPermissions.value = objectMetadata.value.permissions || null
    } else {
      objectMetadata.value = null
      metadataPermissions.value = null
    }

    if (runtimeResult.status === 'rejected' && metadataResult.status === 'rejected') {
      const runtimeError = runtimeResult.reason instanceof Error ? runtimeResult.reason.message : ''
      const metadataError = metadataResult.reason instanceof Error ? metadataResult.reason.message : ''
      loadError.value = metadataError || runtimeError || t('common.messages.loadFailed')
      return
    }

    if (isEdit.value && !canView.value) {
      loadError.value = t('common.messages.permissionDenied')
      return
    }

    if (isEdit.value) {
      const recordResponse = await apiClient.value.get<Record<string, unknown>>(props.recordId)
      const resolvedRecord =
        recordResponse &&
        typeof recordResponse === 'object' &&
        'data' in recordResponse &&
        recordResponse.data &&
        typeof recordResponse.data === 'object'
          ? recordResponse.data as Record<string, unknown>
          : (recordResponse as Record<string, unknown>)
      formData.value = resolvedRecord || {}
    }

    await nextTick()
    isDirty.value = false
  } catch (error: any) {
    loadError.value = error?.message || t('common.messages.operationFailed')
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    void loadData()
  }
})

watch([() => props.objectCode, () => props.recordId], () => {
  if (visible.value) {
    void loadData()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})
</script>

<style scoped lang="scss">
.context-container {
  &__content {
    height: 100%;
    padding: 0;
    overflow-y: auto;
    overflow-x: hidden;
  }

  &__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
  }

  .dirty-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--sys-color-text-secondary);

    .el-icon {
      font-size: 16px;
      color: var(--sys-color-warning);
    }
  }

  .footer-right {
    display: flex;
    gap: 12px;
  }
}

:deep(.context-dialog) {
  margin-top: 5vh;
  margin-bottom: 5vh;
  height: 90vh;
  display: flex;
  flex-direction: column;
  
  .el-dialog__body {
    flex: 1;
    overflow: hidden;
    padding: 20px;
    display: flex;
    flex-direction: column;
  }
}
</style>
