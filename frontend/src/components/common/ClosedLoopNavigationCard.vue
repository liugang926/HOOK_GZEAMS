<template>
  <el-card
    v-if="visibleItems.length > 0"
    class="closed-loop-nav-card"
  >
    <template #header>
      <div class="closed-loop-nav-card__header">
        <span>{{ title }}</span>
        <span
          v-if="hint"
          class="closed-loop-nav-card__hint"
        >
          {{ hint }}
        </span>
      </div>
    </template>

    <div class="closed-loop-nav-card__actions">
      <el-button
        v-for="item in visibleItems"
        :key="item.key || item.label"
        :type="item.type || 'primary'"
        :plain="item.plain ?? true"
        :disabled="item.disabled"
        @click="emit('select', item)"
      >
        {{ item.label }}
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ClosedLoopNavigationItem } from '@/composables/useClosedLoopNavigation'

const props = withDefaults(
  defineProps<{
    title?: string
    hint?: string
    items: ClosedLoopNavigationItem[]
  }>(),
  {
    title: 'Closed-loop Navigation',
    hint: '',
  }
)

const emit = defineEmits<{
  (e: 'select', item: ClosedLoopNavigationItem): void
}>()

const visibleItems = computed(() => {
  return (props.items || []).filter((item) => item && item.visible !== false)
})
</script>

<style scoped lang="scss">
.closed-loop-nav-card__header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.closed-loop-nav-card__hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.closed-loop-nav-card__actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
