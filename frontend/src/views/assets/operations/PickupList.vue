<template>
  <div class="pickup-list page-container">
    <BaseListPage
      ref="listRef"
      title="资产领用单"
      object-code="asset_pickup_list"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchPickupList"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          新建领用单
        </el-button>
      </template>

      <template #status="{ row }">
        <el-tag
          :type="getStatusType(row.status)"
          class="status-tag"
          :class="`status-${row.status}`"
        >
          {{ row.statusLabel || getStatusLabel(row.status) }}
        </el-tag>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleView(row)"
        >
          查看
        </el-button>
        <el-button
          v-if="['draft', 'pending'].includes(row.status)"
          link
          type="primary"
          @click="handleEdit(row)"
        >
          编辑
        </el-button>
        <el-button
          v-if="['draft', 'pending'].includes(row.status)"
          link
          type="warning"
          @click="handleCancel(row)"
        >
          取消
        </el-button>
      </template>
    </BaseListPage>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPickupList, cancelPickup } from '@/api/assets/pickup'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()
const listRef = ref()

// API Wrapper to adapt to BaseListPage expectation if needed
// Assuming BaseListPage passes { page, pageSize, ...filters } and expects { results, count }
const fetchPickupList = async (params: any) => {
  // Convert standard params to what getPickupList expects (snake_case)
  const apiParams = {
    ...params,
    page_size: params.pageSize
  }
  const res = await getPickupList(apiParams)
  return {
    results: res.items || res.results || [],
    count: res.total || res.count || 0
  }
}

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '草稿', value: 'draft' },
      { label: '待审批', value: 'pending' },
      { label: '已批准', value: 'approved' },
      { label: '已拒绝', value: 'rejected' },
      { label: '已完成', value: 'completed' }
    ]
  },
  {
    prop: 'search',
    label: '搜索',
    type: 'text',
    placeholder: '领用单号/申请人'
  }
]

const columns: TableColumn[] = [
  { prop: 'pickupNo', label: '领用单号', width: 150 },
  { prop: 'applicant.realName', label: '申请人', width: 100 },
  { prop: 'department.name', label: '领用部门', width: 120 },
  { prop: 'pickupDate', label: '领用日期', width: 110 },
  { prop: 'status', label: '状态', width: 100, slot: 'status' },
  { prop: 'itemsCount', label: '资产数量', width: 100, align: 'center' },
  { prop: 'createdAt', label: '创建时间', width: 160 }
]

const getStatusType = (status: string) => {
  const map: any = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    completed: 'success',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: any = {
    draft: '草稿',
    pending: '待审批',
    approved: '已批准',
    rejected: '已拒绝',
    completed: '已完成',
    cancelled: '已取消'
  }
  return map[status] || status
}

const handleCreate = () => {
  router.push('/assets/operations/pickup/create')
}

const handleView = (row: any) => {
  router.push(`/assets/operations/pickup/${row.id}`)
}

const handleEdit = (row: any) => {
  router.push(`/assets/operations/pickup/${row.id}/edit`)
}

const handleCancel = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要取消此领用单吗？', '确认操作', { type: 'warning' })
    await cancelPickup(row.id)
    ElMessage.success('已取消')
    listRef.value?.refresh()
  } catch {
    // cancelled
  }
}
</script>

<style scoped lang="scss">
.pickup-list {
  // Using global styles now, minimal local overrides
}
</style>
