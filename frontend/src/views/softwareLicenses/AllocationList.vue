<!-- frontend/src/views/softwareLicenses/AllocationList.vue -->

<template>
  <BaseListPage
    title="许可证分配记录"
    :api="licenseAllocationApi.list"
    :table-columns="columns"
    :search-fields="searchFields"
    @row-click="handleRowClick"
  >
    <template #toolbar>
      <el-button
        type="primary"
        @click="handleCreate"
      >
        <el-icon><Plus /></el-icon>
        新建分配
      </el-button>
    </template>
    <template #isActive="{ row }">
      <el-tag :type="row.isActive ? 'success' : 'info'">
        {{ row.isActive ? '已分配' : '已解除' }}
      </el-tag>
    </template>
    <template #actions="{ row }">
      <el-button
        v-if="row.isActive"
        link
        type="warning"
        @click.stop="handleDeallocate(row)"
      >
        解除分配
      </el-button>
      <el-text
        v-else
        type="info"
      >
        已解除
      </el-text>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { licenseAllocationApi } from '@/api/softwareLicenses'
import type { TableColumn, SearchField } from '@/types/common'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()

const columns: TableColumn[] = [
  { prop: 'softwareName', label: '软件', minWidth: 150 },
  { prop: 'licenseNo', label: '许可证编号', width: 150 },
  { prop: 'assetCode', label: '资产编码', width: 130 },
  { prop: 'assetName', label: '资产名称', minWidth: 150 },
  { prop: 'allocatedDate', label: '分配日期', width: 120 },
  { prop: 'allocatedByName', label: '分配人', width: 100 },
  { prop: 'isActive', label: '状态', width: 100, slot: true },
  { prop: 'actions', label: '操作', width: 120, slot: true, fixed: 'right' }
]

const searchFields: SearchField[] = [
  { prop: 'search', label: '搜索', placeholder: '软件/资产' },
  { prop: 'isActive', label: '状态', type: 'select', options: [
    { label: '已分配', value: true },
    { label: '已解除', value: false }
  ]}
]

const handleRowClick = (row: any) => {
  // Show detail dialog
}

const handleCreate = () => {
  router.push('/software-licenses/licenses')
}

const handleDeallocate = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要解除 ${row.softwareName} 在 ${row.assetName} 上的分配吗？`,
      '确认解除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await licenseAllocationApi.deallocate(row.id)
    ElMessage.success('解除成功')
    // Refresh is handled by BaseListPage
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '解除失败')
    }
  }
}
</script>
