<template>
  <el-tab-pane name="tasks">
    <template #label>
      <span>{{ $t('portal.tabs.myTasks') }}</span>
      <el-badge
        v-if="pendingCount > 0"
        :value="pendingCount"
        type="danger"
        class="tab-badge"
      />
    </template>

    <div class="tab-toolbar">
      <el-button
        :icon="Refresh"
        @click="emit('refresh')"
      >
        {{ $t('common.actions.refresh') }}
      </el-button>
    </div>

    <div
      v-if="tasks.length === 0 && !loading"
      class="no-tasks"
    >
      <el-empty :description="$t('portal.tasks.empty')" />
    </div>

    <div
      v-loading="loading"
      class="task-cards"
    >
      <div
        v-for="task in tasks"
        :key="task.id"
        class="task-card"
        @click="emit('open', task)"
      >
        <div class="task-card-left">
          <el-tag
            type="warning"
            size="small"
            class="task-type"
          >
            {{ getPortalTaskTypeLabel(task, t) }}
          </el-tag>
          <div class="task-title">
            {{ getPortalTaskTitle(task) }}
          </div>
          <div class="task-meta">
            <span>{{ $t('portal.tasks.initiator') }}: {{ getPortalTaskInitiator(task) }}</span>
            <span class="meta-sep">-</span>
            <span>{{ formatDate(getPortalTaskTime(task)) }}</span>
          </div>
        </div>
        <div class="task-card-right">
          <el-button
            type="success"
            size="small"
            @click.stop="emit('approve', task)"
          >
            {{ $t('portal.tasks.approve') }}
          </el-button>
          <el-button
            type="danger"
            size="small"
            @click.stop="emit('reject', task)"
          >
            {{ $t('portal.tasks.reject') }}
          </el-button>
        </div>
      </div>
    </div>

    <el-pagination
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      class="mt-16"
      @update:current-page="emit('update:currentPage', $event)"
      @update:page-size="emit('update:pageSize', $event)"
      @current-change="emit('refresh')"
    />
  </el-tab-pane>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Refresh } from '@element-plus/icons-vue'

import type { PortalTaskRecord } from '@/types/portal'
import { formatDate } from '@/utils/dateFormat'

import {
  getPortalTaskInitiator,
  getPortalTaskTime,
  getPortalTaskTitle,
  getPortalTaskTypeLabel,
} from './portalTaskModel'

defineProps<{
  currentPage: number
  loading: boolean
  pageSize: number
  pendingCount: number
  tasks: PortalTaskRecord[]
  total: number
}>()

const emit = defineEmits<{
  approve: [task: PortalTaskRecord]
  open: [task: PortalTaskRecord]
  reject: [task: PortalTaskRecord]
  refresh: []
  'update:currentPage': [value: number]
  'update:pageSize': [value: number]
}>()

const { t } = useI18n()
</script>

<style scoped>
.tab-badge { margin-left: 4px; }
.tab-toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.mt-16 { margin-top: 16px; }

.no-tasks { padding: 40px 0; }
.task-cards { display: flex; flex-direction: column; gap: 10px; }
.task-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
  background: #fff;
}
.task-card:hover { border-color: #409eff; box-shadow: 0 2px 8px rgba(64,158,255,0.15); }
.task-card-left { flex: 1; min-width: 0; }
.task-type { margin-bottom: 6px; }
.task-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 6px 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.task-meta { font-size: 12px; color: #909399; }
.meta-sep { margin: 0 6px; }
.task-card-right { display: flex; gap: 6px; flex-shrink: 0; margin-left: 16px; }
</style>
