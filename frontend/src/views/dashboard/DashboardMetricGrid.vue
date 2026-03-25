<template>
  <el-row :gutter="20">
    <el-col
      v-for="card in cards"
      :key="card.id"
      :span="6"
    >
      <el-card
        shadow="hover"
        class="data-card"
      >
        <div class="card-header">
          <span>{{ card.label }}</span>
          <el-tag :type="card.tagType">
            {{ card.tagLabel }}
          </el-tag>
        </div>
        <div
          class="card-value"
          :class="card.valueClass"
        >
          {{ card.value }}
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import type { DashboardMetricCard } from './dashboardCardModel'

defineProps<{
  cards: DashboardMetricCard[]
}>()
</script>

<style scoped>
.data-card { height: 120px; display: flex; flex-direction: column; justify-content: center; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-size: 14px; color: #909399; }
.card-value { font-size: 28px; font-weight: bold; margin-top: 8px; color: #303133; }
.text-danger { color: #F56C6C; }
</style>
