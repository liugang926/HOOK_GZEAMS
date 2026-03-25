<template>
  <el-card shadow="hover">
    <template #header>
      <span>{{ title }}</span>
    </template>
    <div
      :ref="setChartRef"
      class="chart-body"
    />
  </el-card>
</template>

<script setup lang="ts">
import type { VNodeRef } from 'vue'

defineProps<{
  setChartRef: VNodeRef
  title: string
}>()
</script>

<style scoped>
.chart-body { height: 300px; }
</style>
