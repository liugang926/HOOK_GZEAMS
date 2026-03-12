<template>
  <div class="designer-property-section-heading">
    <span class="designer-property-section-heading__label">{{ label }}</span>
    <span class="designer-property-section-heading__count">{{ count }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  count: number
}>()
</script>

<style scoped>
.designer-property-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  min-width: 0;
  padding-right: 8px;
}

.designer-property-section-heading__label {
  min-width: 0;
  color: #1f2937;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.designer-property-section-heading__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  color: #4b5563;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}
</style>
