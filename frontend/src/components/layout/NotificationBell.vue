<template>
  <div class="notification-bell">
    <el-popover
      placement="bottom"
      :width="300"
      trigger="click"
      popper-class="notification-popover"
    >
      <template #reference>
        <el-badge
          :value="store.count"
          :hidden="store.count === 0"
          class="bell-badge"
        >
          <el-button
            link
            :icon="Bell"
            class="bell-icon"
          />
        </el-badge>
      </template>
      
      <div class="notification-list">
        <div class="list-header">
          <span>待办任务</span>
          <el-link
            type="primary"
            :underline="false"
            @click="viewAll"
          >
            查看全部
          </el-link>
        </div>
        
        <el-divider style="margin: 8px 0" />
        
        <div
          v-if="store.recentTasks && store.recentTasks.length > 0"
          class="task-items"
        >
          <div 
            v-for="task in store.recentTasks" 
            :key="task.id" 
            class="task-item"
            @click="viewTask(task)"
          >
            <div class="task-title">
              {{ task.title || '无标题任务' }}
            </div>
            <div class="task-meta">
              <span class="process-name">{{ task.process_name }}</span>
              <span class="time">{{ formatDate(task.create_time) }}</span>
            </div>
          </div>
        </div>
        <div
          v-else
          class="empty-list"
        >
          <el-empty
            description="暂无待办"
            :image-size="60"
          />
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Bell } from '@element-plus/icons-vue'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const store = useNotificationStore()

const viewAll = () => {
  router.push('/workflow/tasks')
}

const viewTask = (task: any) => {
  router.push(`/workflow/task/${task.id}`)
}

const formatDate = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString()
}

onMounted(() => {
  store.startPolling()
})

onUnmounted(() => {
  store.stopPolling()
})
</script>

<style scoped lang="scss">
.notification-bell {
  margin-right: 20px;
  display: flex;
  align-items: center;
}

.bell-badge {
  display: flex;
  align-items: center;
}

.bell-icon {
  font-size: 20px;
  color: #606266;
  
  &:hover {
    color: #409eff;
  }
}

.notification-list {
  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 4px;
    font-size: 14px;
    color: #303133;
    font-weight: 500;
  }
}

.task-item {
  padding: 8px 4px;
  cursor: pointer;
  border-radius: 4px;
  
  &:hover {
    background-color: #f5f7fa;
  }
  
  .task-title {
    font-size: 14px;
    color: #303133;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .task-meta {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #909399;
  }
}

.empty-list {
  padding: 10px 0;
}
</style>
