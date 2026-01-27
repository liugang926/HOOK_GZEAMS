<!-- frontend/src/views/softwareLicenses/SoftwareCatalog.vue -->

<template>
  <BaseListPage
    title="软件目录"
    :api="softwareApi.list"
    :table-columns="columns"
    :search-fields="searchFields"
    :batch-actions="batchActions"
    @row-click="handleRowClick"
  >
    <template #toolbar>
      <el-button
        type="primary"
        @click="handleCreate"
      >
        <el-icon><Plus /></el-icon>
        新建软件
      </el-button>
    </template>
    <template #softwareType="{ row }">
      <el-tag :type="getSoftwareTypeColor(row.softwareType)">
        {{ getSoftwareTypeLabel(row.softwareType) }}
      </el-tag>
    </template>
    <template #isActive="{ row }">
      <el-tag :type="row.isActive ? 'success' : 'info'">
        {{ row.isActive ? '启用' : '停用' }}
      </el-tag>
    </template>
    <template #actions="{ row }">
      <el-button
        link
        type="primary"
        @click.stop="handleEdit(row)"
      >
        编辑
      </el-button>
      <el-button
        link
        type="primary"
        @click.stop="handleViewLicenses(row)"
      >
        许可证
      </el-button>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { softwareApi } from '@/api/softwareLicenses'
import type { TableColumn, SearchField } from '@/types/common'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()

const columns: TableColumn[] = [
  { prop: 'code', label: '代码', width: 120 },
  { prop: 'name', label: '软件名称', minWidth: 180 },
  { prop: 'version', label: '版本', width: 100 },
  { prop: 'vendor', label: '厂商', width: 150 },
  { prop: 'softwareType', label: '类型', width: 120, slot: true },
  { prop: 'isActive', label: '状态', width: 100, slot: true },
  { prop: 'actions', label: '操作', width: 150, slot: true, fixed: 'right' }
]

const searchFields: SearchField[] = [
  { prop: 'search', label: '搜索', placeholder: '代码/名称/厂商' },
  { prop: 'softwareType', label: '类型', type: 'select', options: [
    { label: '操作系统', value: 'os' },
    { label: '办公软件', value: 'office' },
    { label: '专业软件', value: 'professional' },
    { label: '开发工具', value: 'development' },
    { label: '安全软件', value: 'security' },
    { label: '数据库', value: 'database' },
    { label: '其他', value: 'other' }
  ]},
  { prop: 'isActive', label: '状态', type: 'select', options: [
    { label: '启用', value: true },
    { label: '停用', value: false }
  ]}
]

const batchActions = [
  {
    label: '批量删除',
    type: 'danger' as const,
    action: async (selectedRows: any[]) => {
      const ids = selectedRows.map(row => row.id)
      await softwareApi.batchDelete(ids)
    },
    confirm: true,
    confirmMessage: '确定要删除选中的软件吗？'
  }
]

const getSoftwareTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    os: '操作系统',
    office: '办公软件',
    professional: '专业软件',
    development: '开发工具',
    security: '安全软件',
    database: '数据库',
    other: '其他'
  }
  return labels[type] || type
}

const getSoftwareTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    os: 'primary',
    office: 'success',
    professional: 'warning',
    development: 'info',
    security: 'danger',
    database: '',
    other: 'info'
  }
  return colors[type] || ''
}

const handleRowClick = (row: any) => {
  // Navigate to detail or edit
}

const handleCreate = () => {
  router.push('/software-licenses/software/create')
}

const handleEdit = (row: any) => {
  router.push(`/software-licenses/software/${row.id}/edit`)
}

const handleViewLicenses = (row: any) => {
  router.push(`/software-licenses/licenses?software=${row.code}`)
}
</script>
