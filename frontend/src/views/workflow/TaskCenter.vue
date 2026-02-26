<template>
  <div class="task-center">
    <div class="page-header">
      <h3>{{ $t('workflow.taskCenter.title') }}</h3>
    </div>

    <el-tabs
      v-model="activeTab"
      @tab-click="handleTabClick"
    >
      <el-tab-pane
        :label="$t('workflow.taskCenter.tabs.pending')"
        name="pending"
      >
        <el-table
          v-loading="loading"
          :data="pendingTasks"
          border
        >
          <el-table-column
            prop="title"
            :label="$t('workflow.columns.taskTitle')"
          />
          <el-table-column
            prop="process_name"
            :label="$t('workflow.columns.processType')"
          />
          <el-table-column
            prop="create_time"
            :label="$t('workflow.columns.receiveTime')"
          />
          <el-table-column
            prop="initiator"
            :label="$t('workflow.columns.initiator')"
          />
          <el-table-column :label="$t('workflow.columns.operation')">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="handleProcess(row)"
              >
                {{ $t('workflow.actions.process') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane
        :label="$t('workflow.taskCenter.tabs.processed')"
        name="processed"
      >
        <el-table
          v-loading="loading"
          :data="processedTasks"
          border
        >
          <el-table-column
            prop="title"
            :label="$t('workflow.columns.taskTitle')"
          />
          <el-table-column
            prop="process_name"
            :label="$t('workflow.columns.processType')"
          />
          <el-table-column
            prop="process_time"
            :label="$t('workflow.columns.processTime')"
          />
          <el-table-column
            prop="result"
            :label="$t('workflow.columns.result')"
          />
          <el-table-column :label="$t('workflow.columns.operation')">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="handleView(row)"
              >
                {{ $t('common.actions.view') }}
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
