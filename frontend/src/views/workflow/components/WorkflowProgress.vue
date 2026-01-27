<template>
  <div class="workflow-progress">
    <el-steps
      :active="activeStep"
      finish-status="success"
      align-center
    >
      <el-step 
        v-for="(node, index) in steps" 
        :key="index" 
        :title="node.name" 
        :description="node.description" 
      />
    </el-steps>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  instance: any
}>()

// Mock logic: derive steps from instance data
const steps = computed(() => {
    // In real app, fetch def or process metadata
    return [
        { name: '开始', description: props.instance.start_time },
        { name: '审批中', description: '当前节点' },
        { name: '结束', description: '待完成' }
    ]
})

const activeStep = computed(() => {
    return 1 // Mock
})
</script>

<style scoped>
.workflow-progress {
    padding: 20px 0;
}
</style>
