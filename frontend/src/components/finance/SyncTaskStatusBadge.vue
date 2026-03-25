<template>
  <div
    v-if="visible"
    class="sync-task-status-badge"
  >
    <span
      v-if="showTaskId && syncTaskId"
      class="task-id"
    >
      {{ syncTaskId }}
    </span>
    <el-tag
      size="small"
      :type="tagType"
    >
      {{ statusDisplay || status || '-' }}
    </el-tag>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getSyncTaskStatusType } from '@/utils/syncTaskStatus'

interface Props {
  syncTaskId?: string
  status?: string
  statusDisplay?: string
  showTaskId?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  syncTaskId: '',
  status: '',
  statusDisplay: '',
  showTaskId: true,
})

const visible = computed(() => Boolean(props.status || props.syncTaskId))
const tagType = computed(() => getSyncTaskStatusType(props.status))
</script>

<style scoped>
.sync-task-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.task-id {
  font-size: 12px;
  color: #606266;
}
</style>
