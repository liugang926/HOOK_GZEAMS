<template>
  <div class="barcode-field">
    <div
      v-if="modelValue"
      class="barcode-display"
    >
      <el-image
        :src="barcodeUrl"
        :preview-src-list="[barcodeUrl]"
        fit="contain"
        class="barcode-image"
      >
        <template #error>
          <div class="image-error">
            <el-icon><Picture /></el-icon>
            <span>条形码生成失败</span>
          </div>
        </template>
      </el-image>
      <el-text class="barcode-value">
        {{ modelValue }}
      </el-text>
    </div>
    <el-empty
      v-else
      description="暂无条形码"
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

// Generate barcode URL using a public API
const barcodeUrl = computed(() => {
  if (!props.modelValue) return ''
  const value = encodeURIComponent(props.modelValue)
  const width = props.field.width || 200
  const height = props.field.height || 50
  return `https://barcode.tec-it.com/barcode.ashx?data=${value}&code=Code128&multiple-barcodes=false&translate-esc=false&unit=Fit&dpi=96&imagetype=Gif&rotation=0&color=%23000000&bgcolor=%23ffffff&qunit=Mm&quiet=0&quietzone=0`
})
</script>

<style scoped>
.barcode-field {
  display: flex;
  align-items: center;
}

.barcode-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.barcode-image {
  width: 200px;
  height: 60px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
}

.barcode-value {
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  color: var(--el-text-color-primary);
  letter-spacing: 2px;
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
