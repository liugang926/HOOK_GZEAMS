<template>
  <ElPopover
    v-model:visible="popoverVisible"
    placement="bottom-start"
    :width="332"
    trigger="click"
    popper-class="menu-management-icon-popover"
  >
    <div class="icon-library-panel">
      <button
        v-for="icon in availableIcons"
        :key="icon"
        type="button"
        class="icon-library-button"
        :class="{ selected: modelValue === icon }"
        @click.stop="pickIcon(icon)"
      >
        <span class="icon-library-glyph">
          <el-icon
            v-if="resolveIcon(icon)"
            :size="18"
          >
            <component :is="resolveIcon(icon)" />
          </el-icon>
        </span>
        <span class="icon-library-name">{{ icon }}</span>
      </button>
    </div>
    <template #reference>
      <button
        type="button"
        class="icon-picker-trigger"
        @click.stop
      >
        <span
          class="icon-preview"
          :title="modelValue"
        >
          <el-icon
            v-if="resolveIcon(modelValue)"
            :size="18"
          >
            <component :is="resolveIcon(modelValue)" />
          </el-icon>
          <span v-else>{{ modelValue.slice(0, 1) }}</span>
        </span>
        <span class="icon-picker-text">
          <span class="icon-picker-label">{{ modelValue || placeholder }}</span>
          <span class="icon-picker-hint">选择图标</span>
        </span>
        <span class="icon-picker-caret">⌄</span>
      </button>
    </template>
  </ElPopover>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElPopover } from 'element-plus'

defineProps<{
  modelValue: string
  availableIcons: string[]
  placeholder: string
  resolveIcon: (iconName: string) => unknown
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void
}>()

const popoverVisible = ref(false)

const pickIcon = (icon: string) => {
  emit('update:modelValue', icon)
  popoverVisible.value = false
}
</script>

<style scoped lang="scss">
.icon-picker-trigger {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  width: 100%;
  min-height: 40px;
  padding: 0 12px 0 0;
  border: 1px solid #d8e1ee;
  border-radius: 12px;
  background: #ffffff;
  cursor: pointer;
  color: #10203a;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.icon-picker-trigger:hover {
  border-color: rgba(16, 32, 58, 0.24);
}

.icon-picker-trigger:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.12);
}

.icon-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 11px 0 0 11px;
  border-right: 1px solid #d8e1ee;
  background: #f8fbff;
  color: #10203a;
}

.icon-picker-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  text-align: left;
}

.icon-picker-label,
.icon-picker-hint,
.icon-library-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.icon-picker-label {
  font-size: 14px;
  font-weight: 700;
}

.icon-picker-hint {
  font-size: 11px;
  color: #71839b;
}

.icon-picker-caret {
  color: #71839b;
  font-size: 14px;
  line-height: 1;
}

.icon-library-panel {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  max-height: 240px;
  overflow: auto;
}

.icon-library-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-height: 72px;
  padding: 10px 8px;
  border: 1px solid #d8e1ee;
  border-radius: 14px;
  background: #ffffff;
  color: #10203a;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}

.icon-library-button:hover {
  border-color: rgba(16, 32, 58, 0.24);
  background: #f8fbff;
  transform: translateY(-1px);
}

.icon-library-button.selected {
  border-color: rgba(16, 32, 58, 0.4);
  background: #eef4ff;
}

.icon-library-glyph {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 10px;
  background: #f8fbff;
}

.icon-library-name {
  width: 100%;
  font-size: 11px;
  text-align: center;
  color: #52657f;
}

:global(.menu-management-icon-popover) {
  padding: 12px;
}

:global(.menu-management-icon-popover .el-popper__arrow) {
  display: none;
}
</style>
