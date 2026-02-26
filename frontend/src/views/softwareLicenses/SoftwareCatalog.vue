<!-- frontend/src/views/softwareLicenses/SoftwareCatalog.vue -->

<template>
  <BaseListPage
    :title="$t('softwareLicenses.catalog.title')"
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
        {{ $t('softwareLicenses.catalog.add') }}
      </el-button>
    </template>
    <template #actions="{ row }">
      <el-button
        link
        type="primary"
        @click.stop="handleEdit(row)"
      >
        {{ $t('common.actions.edit') }}
      </el-button>
      <el-button
        link
        type="primary"
        @click.stop="handleViewLicenses(row)"
      >
        {{ $t('softwareLicenses.catalog.viewLicenses') }}
      </el-button>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { softwareApi } from '@/api/softwareLicenses'
import type { TableColumn, SearchField } from '@/types/common'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()
const { t } = useI18n()

const columns = computed<TableColumn[]>(() => [
  { prop: 'code', label: t('softwareLicenses.catalog.fields.code'), width: 120 },
  { prop: 'name', label: t('softwareLicenses.catalog.fields.name'), minWidth: 180 },
  { prop: 'version', label: t('softwareLicenses.catalog.fields.version'), width: 100 },
  { prop: 'vendor', label: t('softwareLicenses.catalog.fields.vendor'), width: 150 },
  { prop: 'softwareType', label: t('softwareLicenses.catalog.fields.type'), width: 120, tagType: (row: any) => getSoftwareTypeColor(row.softwareType), format: (value: any) => getSoftwareTypeLabel(value) },
  { prop: 'isActive', label: t('softwareLicenses.catalog.fields.status'), width: 100, tagType: (row: any) => (row.isActive ? 'success' : 'info'), format: (value: any) => (value ? t('common.status.active') : t('common.status.inactive')) },
  { prop: 'actions', label: t('common.labels.operation', '操作'), width: 150, slot: true, fixed: 'right' }
])

const searchFields = computed<SearchField[]>(() => [
  { prop: 'search', label: t('common.actions.search'), placeholder: t('softwareLicenses.catalog.placeholders.search') },
  { prop: 'softwareType', label: t('softwareLicenses.catalog.fields.type'), type: 'select', options: [
    { label: t('softwareLicenses.catalog.types.os'), value: 'os' },
    { label: t('softwareLicenses.catalog.types.office'), value: 'office' },
    { label: t('softwareLicenses.catalog.types.professional'), value: 'professional' },
    { label: t('softwareLicenses.catalog.types.development'), value: 'development' },
    { label: t('softwareLicenses.catalog.types.security'), value: 'security' },
    { label: t('softwareLicenses.catalog.types.database'), value: 'database' },
    { label: t('softwareLicenses.catalog.types.other'), value: 'other' }
  ]},
  { prop: 'isActive', label: t('softwareLicenses.catalog.fields.status'), type: 'select', options: [
    { label: t('common.status.active'), value: true },
    { label: t('common.status.inactive'), value: false }
  ]}
])

const batchActions = computed(() => [
  {
    label: t('common.actions.batchDelete', '批量删除'),
    type: 'danger' as const,
    action: async (selectedRows: any[]) => {
      const ids = selectedRows.map(row => row.id)
      await softwareApi.batchDelete(ids)
    },
    confirm: true,
    confirmMessage: t('softwareLicenses.catalog.messages.deleteConfirm')
  }
])

const getSoftwareTypeLabel = (type: string) => {
  return t(`softwareLicenses.catalog.types.${type}`)
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
