<template>
  <div class="field-error-fallback">
    <el-tooltip
      :content="errorDetail"
      placement="top"
      :disabled="!errorDetail"
    >
      <div class="field-error-fallback__body">
        <el-icon class="field-error-fallback__icon">
          <WarningFilled />
        </el-icon>
        <span class="field-error-fallback__label">{{ fieldLabel }}</span>
        <span class="field-error-fallback__msg">{{ t('common.messages.loadFailed') }}</span>
        <el-button
          class="field-error-fallback__retry"
          size="small"
          type="primary"
          link
          @click="$emit('retry')"
        >
          {{ t('system.fieldDefinition.actions.retry') }}
        </el-button>
      </div>
    </el-tooltip>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { WarningFilled } from '@element-plus/icons-vue'

defineProps<{
  fieldLabel?: string
  errorDetail?: string
}>()

defineEmits<{
  (e: 'retry'): void
}>()

const { t } = useI18n()
</script>

<style scoped>
.field-error-fallback {
  min-height: 32px;
  display: flex;
  align-items: center;
  border: 1px dashed var(--el-color-danger-light-5, #fab6b6);
  border-radius: var(--sys-radius-base, 6px);
  background: var(--el-color-danger-light-9, #fef0f0);
  padding: 4px 10px;
  font-size: 12px;
  color: var(--el-color-danger, #f56c6c);
  transition: border-color 0.2s;
}

.field-error-fallback:hover {
  border-color: var(--el-color-danger, #f56c6c);
}

.field-error-fallback__body {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  overflow: hidden;
}

.field-error-fallback__icon {
  flex-shrink: 0;
  font-size: 14px;
}

.field-error-fallback__label {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.field-error-fallback__msg {
  color: var(--el-text-color-secondary, #909399);
  white-space: nowrap;
}

.field-error-fallback__retry {
  flex-shrink: 0;
  margin-left: auto;
}
</style>
