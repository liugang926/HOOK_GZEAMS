<template>
  <div class="workflow-list">
    <div class="page-header">
      <h3>工作流管理</h3>
      <el-button
        type="primary"
        @click="$router.push('/admin/workflows/create')"
      >
        创建工作流
      </el-button>
    </div>
    <el-table
      v-loading="loading"
      :data="tableData"
      border
    >
      <el-table-column
        prop="name"
        label="名称"
      />
      <el-table-column
        prop="code"
        label="编码"
      />
      <el-table-column
        prop="business_object"
        label="业务对象"
      />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="$router.push(`/admin/workflows/${row.id}/edit`)"
          >
            编辑
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getWorkflows } from '@/api/workflows'

const tableData = ref([])
const loading = ref(false)

onMounted(async () => {
    loading.value = true
    try {
        const res = await getWorkflows()
        tableData.value = res.results || res.items || []
    } finally {
        loading.value = false
    }
})
</script>

<style scoped>
.workflow-list { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
</style>
