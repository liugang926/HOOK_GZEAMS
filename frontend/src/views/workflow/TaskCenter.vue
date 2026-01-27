<template>
  <div class="task-center">
    <div class="page-header">
      <h3>我的待办</h3>
    </div>

    <el-tabs
      v-model="activeTab"
      @tab-click="handleTabClick"
    >
      <el-tab-pane
        label="待处理"
        name="pending"
      >
        <el-table
          v-loading="loading"
          :data="pendingTasks"
          border
        >
          <el-table-column
            prop="title"
            label="任务标题"
          />
          <el-table-column
            prop="process_name"
            label="流程类型"
          />
          <el-table-column
            prop="create_time"
            label="接收时间"
          />
          <el-table-column
            prop="initiator"
            label="发起人"
          />
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="handleProcess(row)"
              >
                办理
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane
        label="已处理"
        name="processed"
      >
        <el-table
          v-loading="loading"
          :data="processedTasks"
          border
        >
          <el-table-column
            prop="title"
            label="任务标题"
          />
          <el-table-column
            prop="process_name"
            label="流程类型"
          />
          <el-table-column
            prop="process_time"
            label="处理时间"
          />
          <el-table-column
            prop="result"
            label="处理结果"
          />
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="handleView(row)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { workflowNodeApi } from '@/api/workflow'

const router = useRouter()
const activeTab = ref('pending')
const loading = ref(false)
const pendingTasks = ref([])
const processedTasks = ref([])

const fetchData = async () => {
    loading.value = true
    try {
        if (activeTab.value === 'pending') {
            const res = await workflowNodeApi.getMyTasks({ page: 1, pageSize: 20, status: 'pending' })
            pendingTasks.value = res.results
        } else {
            // Backend might support "processed" or "history" status, or different endpoint
            // For now assuming getMyTasks handles handled tasks or we use a different API
            // Ideally workflowNodeApi.getMyHistory? 
            // If not available, we leave empty or mock for now as per plan focus on pending
             const res = await workflowNodeApi.getMyTasks({ page: 1, pageSize: 20, status: 'completed' })
             processedTasks.value = res.results
        }
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const handleTabClick = () => {
    fetchData()
}

const handleProcess = (row: any) => {
    router.push(`/workflow/task/${row.id}`)
}

const handleView = (row: any) => {
    router.push(`/workflow/process/${row.process_instance_id}`)
}

onMounted(() => {
    fetchData()
})
</script>

<style scoped>
.task-center { padding: 20px; }
</style>
