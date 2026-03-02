<template>
  <el-dropdown
    trigger="click"
    @command="handleCommand"
  >
    <span class="locale-trigger">
      <span style="font-size: 16px;">🌐</span>
      <span class="locale-label">{{ currentLabel }}</span>
      <el-icon class="el-icon--right"><ArrowDown /></el-icon>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="locale in locales"
          :key="locale.value"
          :command="locale.value"
          :disabled="locale.value === currentLocale"
        >
          <span :class="{ 'is-active': locale.value === currentLocale }">
            {{ locale.label }}
          </span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useLocaleStore } from '@/stores/locale'
import type { LocaleType } from '@/locales'
import { ArrowDown } from '@element-plus/icons-vue'

const localeStore = useLocaleStore()
const currentLocale = computed(() => localeStore.currentLocale)

const locales: Array<{ value: LocaleType; label: string }> = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'en-US', label: 'English' }
]

const currentLabel = computed(
  () => locales.find((l) => l.value === currentLocale.value)?.label || '语言'
)

const handleCommand = (locale: LocaleType) => {
  localeStore.setLocale(locale)
}
</script>

<style scoped>
.locale-trigger {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 12px;
  color: #606266;
  transition: color 0.3s;
}

.locale-trigger:hover {
  color: #409eff;
}

.locale-label {
  margin-left: 4px;
  font-size: 14px;
}

.is-active {
  color: #409eff;
  font-weight: 600;
}
</style>
