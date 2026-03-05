<template>
  <div class="workflow-list">
    <div class="page-header">
      <h3>{{ t('workflow.title') }}</h3>
      <el-button
        type="primary"
        @click="$router.push('/admin/workflows/create')"
      >
        {{ t('common.actions.create') }}
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
    >
      <el-table-column
        prop="name"
        :label="t('workflow.fields.processName')"
      />
      <el-table-column
        prop="code"
        :label="t('workflow.fields.processCode')"
      />
      <el-table-column
        prop="business_object"
        :label="t('workflow.columns.processType')"
      />
      <el-table-column :label="t('workflow.columns.operation')">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="$router.push(`/admin/workflows/${row.id}/edit`)"
          >
            {{ t('common.actions.edit') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getWorkflows } from '@/api/workflows'

const { t } = useI18n()

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
.workflow-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
