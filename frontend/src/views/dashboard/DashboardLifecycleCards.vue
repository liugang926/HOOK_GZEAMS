<template>
  <el-row
    :gutter="20"
    class="mt-12"
  >
    <el-col
      v-for="card in cards"
      :key="card.id"
      :span="6"
    >
      <el-card
        shadow="hover"
        class="data-card lifecycle-card clickable"
        @click="emit('navigate', card.route)"
      >
        <div class="card-header">
          <span>{{ card.label }}</span>
          <el-icon
            class="card-icon"
            :color="card.iconColor"
          >
            <component :is="iconMap[card.icon]" />
          </el-icon>
        </div>
        <div
          class="card-value"
          :class="card.valueClass"
        >
          {{ card.value }}
        </div>
        <div class="card-footer">
          {{ viewAllLabel }} ->
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { Delete, ShoppingCart, Tools, Warning } from '@element-plus/icons-vue'

import type { DashboardLifecycleCard } from './dashboardCardModel'

defineProps<{
  cards: DashboardLifecycleCard[]
  viewAllLabel: string
}>()

const emit = defineEmits<{
  navigate: [route: string]
}>()

const iconMap = {
  purchase: ShoppingCart,
  maintenance: Tools,
  task: Warning,
  disposal: Delete,
} as const
</script>

<style scoped>
.mt-12 { margin-top: 12px; }
.data-card { height: 120px; display: flex; flex-direction: column; justify-content: center; }
.lifecycle-card { height: 130px; }
.clickable { cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }
.clickable:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.12) !important; }

.card-header { display: flex; justify-content: space-between; align-items: center; font-size: 14px; color: #909399; }
.card-icon { font-size: 20px; }
.card-value { font-size: 28px; font-weight: bold; margin-top: 8px; color: #303133; }
.card-footer { font-size: 12px; color: #c0c4cc; margin-top: 4px; }

.text-danger { color: #F56C6C; }
.text-warning { color: #E6A23C; }
.text-primary { color: #409EFF; }
</style>
