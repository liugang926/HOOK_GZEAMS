<template>
  <div class="qr-code-field">
    <div
      v-if="modelValue"
      class="qr-code-display"
    >
      <el-image
        :src="qrCodeUrl"
        :preview-src-list="[qrCodeUrl]"
        fit="contain"
        class="qr-code-image"
      >
        <template #error>
          <div class="image-error">
            <el-icon><Picture /></el-icon>
            <span>二维码生成失败</span>
          </div>
        </template>
      </el-image>
      <el-text
        v-if="showValue"
        class="qr-code-value"
        truncated
      >
        {{ modelValue }}
      </el-text>
    </div>
    <el-empty
      v-else
      description="暂无二维码"
      :image-size="60"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Picture } from '@element-plus/icons-vue'

const props = defineProps({
  field: Object,
  modelValue: String,
  disabled: Boolean
})

const showValue = computed(() => props.field.showValue !== false)

// Generate QR code URL using a public API
const qrCodeUrl = computed(() => {
  if (!props.modelValue) return ''
  const value = encodeURIComponent(props.modelValue)
  const size = props.field.size || 150
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${value}`
})
</script>

<style scoped>
.qr-code-field {
  display: flex;
  align-items: center;
}

.qr-code-display {
  display: flex;
  align-items: center;
  gap: 16px;
}

.qr-code-image {
  width: 150px;
  height: 150px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
}

.qr-code-value {
  max-width: 200px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}
</style>
