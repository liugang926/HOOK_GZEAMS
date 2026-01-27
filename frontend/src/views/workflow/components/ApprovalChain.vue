<template>
  <div class="approval-chain">
    <el-timeline>
      <el-timeline-item
        v-for="(activity, index) in activities"
        :key="index"
        :type="activity.type"
        :color="activity.color"
        :timestamp="activity.timestamp"
      >
        <h4>{{ activity.title }}</h4>
        <p>{{ activity.content }}</p>
        <p
          v-if="activity.comment"
          class="comment"
        >
          意见: {{ activity.comment }}
        </p>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  history: any[]
}>()

const activities = computed(() => {
  return props.history.map(item => ({
    title: item.user_name + ' ' + item.action, // e.g., "Zhang San Approved"
    content: item.node_name,
    timestamp: item.time,
    type: item.action === 'reject' ? 'danger' : 'success',
    color: item.action === 'reject' ? '#F56C6C' : '#67C23A',
    comment: item.comment
  }))
})
</script>

<style scoped>
.comment {
    color: #909399;
    font-size: 12px;
}
</style>
