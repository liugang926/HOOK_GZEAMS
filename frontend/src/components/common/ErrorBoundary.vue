<template>
  <div
    v-if="hasError"
    class="error-boundary-alert"
  >
    <slot
      name="fallback"
      :error="errorMessage"
      :reset="resetBoundary"
      :reset-boundary="resetBoundary"
    >
      <el-alert
        :title="t('common.messages.loadFailed')"
        type="error"
        show-icon
        :closable="false"
      >
        <template #default>
          <div class="error-description">
            {{ errorMessage }}
          </div>
          <div class="error-actions">
            <el-button
              size="small"
              type="primary"
              plain
              @click="resetBoundary"
            >
              {{ t('system.fieldDefinition.actions.retry') }}
            </el-button>
          </div>
        </template>
      </el-alert>
    </slot>
  </div>
  <div
    v-else
    :key="renderKey"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const hasError = ref(false)
const errorMessage = ref('')
const renderKey = ref(0)

const resetBoundary = () => {
  hasError.value = false
  errorMessage.value = ''
  renderKey.value += 1
}

defineExpose({
  resetBoundary
})

onErrorCaptured((err: unknown, _instance, _info) => {
  console.error('[ErrorBoundary] captured rendering error:', err, 'Info:', _info)
  hasError.value = true
  errorMessage.value = err instanceof Error ? err.message : String(err)
  // Return false to prevent the error from propagating up and crashing the entire app
  return false
})
</script>

<style scoped>
.error-boundary-alert {
  margin: 4px 0;
  border-radius: var(--sys-radius-base, 8px);
  border: 1px solid var(--el-color-danger-light-7);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.1);
}

.error-description {
  margin-bottom: 8px;
  word-break: break-all;
}

.error-actions {
  margin-top: 8px;
}
</style>
