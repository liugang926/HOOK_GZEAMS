<template>
  <el-card shadow="hover">
    <template #header>
      <span>{{ title }}</span>
    </template>
    <el-empty
      v-if="!loading && items.length === 0"
      :description="emptyDescription"
      :image-size="60"
    />
    <el-timeline
      v-else
      class="activity-timeline"
    >
      <el-timeline-item
        v-for="item in items"
        :key="item.id"
        :type="item.type"
        :timestamp="item.time"
        placement="top"
        size="small"
      >
        <router-link
          :to="item.url"
          class="activity-link"
        >
          {{ item.title }}
        </router-link>
        <div class="activity-sub">
          {{ item.sub }}
        </div>
      </el-timeline-item>
    </el-timeline>
  </el-card>
</template>

<script setup lang="ts">
import type { DashboardActivityItem } from './dashboardModel'

defineProps<{
  emptyDescription: string
  items: DashboardActivityItem[]
  loading: boolean
  title: string
}>()
</script>

<style scoped>
.activity-timeline { padding: 8px 16px; max-height: 270px; overflow-y: auto; }
.activity-link { font-size: 13px; color: #409EFF; text-decoration: none; }
.activity-link:hover { text-decoration: underline; }
.activity-sub { font-size: 12px; color: #909399; margin-top: 2px; }
</style>
