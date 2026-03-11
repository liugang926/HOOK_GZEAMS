<template>
  <div class="view-switch">
    <button
      type="button"
      class="view-switch-button"
      :class="{ active: current === 'resource' }"
      @click="$emit('change', 'resource')"
    >
      {{ resourceLabel }}
    </button>
    <button
      type="button"
      class="view-switch-button"
      :class="{ active: current === 'layout' }"
      @click="$emit('change', 'layout')"
    >
      {{ layoutLabel }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  current: 'resource' | 'layout'
  resourceLabel: string
  layoutLabel: string
}>()

defineEmits<{
  (event: 'change', value: 'resource' | 'layout'): void
}>()
</script>

<style scoped lang="scss">
.view-switch {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 8px;
  border: 1px solid #d8e1ee;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 248, 255, 0.98) 100%);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
}

.view-switch-button {
  border: 0;
  border-radius: 12px;
  padding: 10px 16px;
  background: transparent;
  color: #51657e;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.view-switch-button.active {
  background: #10203a;
  color: #ffffff;
  box-shadow: 0 10px 20px rgba(16, 32, 58, 0.18);
}
</style>
