<template>
  <el-card
    class="task-card"
    shadow="hover"
    @click="handleClick"
  >
    <div class="header">
      <span class="title">{{ task.title }}</span>
      <el-tag
        size="small"
        :type="statusType"
      >
        {{ task.status }}
      </el-tag>
    </div>
    <div class="content">
      <div class="item">
        <span class="label">流程类型:</span>
        <span class="value">{{ task.process_name }}</span>
      </div>
      <div class="item">
        <span class="label">发起人:</span>
        <span class="value">{{ task.initiator }}</span>
      </div>
      <div class="item">
        <span class="label">时间:</span>
        <span class="value">{{ task.create_time }}</span>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  task: any
}>()

const emit = defineEmits(['click'])

const statusType = computed(() => {
  const map: any = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger'
  }
  // Simplified logic, assume task.status_key or just map by text for now
  return map[props.task.status_key] || 'info'
})

const handleClick = () => {
  emit('click', props.task)
}
</script>

<style scoped>
.task-card {
  cursor: pointer;
  margin-bottom: 15px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.title {
  font-weight: bold;
  font-size: 16px;
}
.item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 14px;
  color: #606266;
}
</style>
