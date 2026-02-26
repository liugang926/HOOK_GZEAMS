<template>
  <div class="business-object-list">
    <BaseListPage
      ref="listRef"
      :title="t('system.businessObject.title')"
      :table-columns="columns"
      :api="fetchList"
    >
      <template #toolbar>
        <el-button
          type="primary"
          @click="handleCreate"
        >
          {{ t('system.businessObject.create') }}
        </el-button>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click.stop="handleFields(row)"
        >
          {{ t('system.businessObject.actions.fields') }}
        </el-button>
        <el-button
          link
          type="primary"
          @click.stop="handleLayouts(row)"
        >
          {{ t('system.businessObject.actions.layouts') }}
        </el-button>
        <el-button
          link
          type="primary"
          @click.stop="handleEdit(row)"
        >
          {{ t('common.actions.edit') }}
        </el-button>
      </template>
    </BaseListPage>

    <BusinessObjectForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="handleRefresh"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn } from '@/types/common'
import { businessObjectApi } from '@/api/system'
import type { BusinessObject } from '@/types/businessObject'
import BusinessObjectForm from './components/BusinessObjectForm.vue'

const router = useRouter()
const { t } = useI18n()

const listRef = ref()
const dialogVisible = ref(false)
const currentRow = ref<BusinessObject | null>(null)

const normalizeBusinessObject = (raw: any, kind?: 'hardcoded' | 'custom'): BusinessObject => {
  const inferredKind: 'hardcoded' | 'custom' =
    kind || (raw?.type === 'hardcoded' ? 'hardcoded' : raw?.type === 'custom' ? 'custom' : 'custom')

  const isHardcoded = raw?.isHardcoded ?? raw?.is_hardcoded ?? inferredKind === 'hardcoded'

  return {
    id: raw?.id || '',
    code: raw?.code || '',
    name: raw?.name || '',
    nameEn: raw?.nameEn ?? raw?.name_en ?? '',
    description: raw?.description ?? '',
    enableWorkflow: raw?.enableWorkflow ?? raw?.enable_workflow ?? false,
    enableVersion: raw?.enableVersion ?? raw?.enable_version ?? false,
    enableSoftDelete: raw?.enableSoftDelete ?? raw?.enable_soft_delete ?? false,
    isHardcoded,
    djangoModelPath: raw?.djangoModelPath ?? raw?.django_model_path ?? raw?.modelPath ?? raw?.model_path ?? '',
    tableName: raw?.tableName ?? raw?.table_name ?? '',
    fieldCount: raw?.fieldCount ?? raw?.field_count,
    layoutCount: raw?.layoutCount ?? raw?.layout_count
  } as BusinessObject
}

const resolveListPayload = (payload: any) => {
  if (Array.isArray(payload)) {
    const results = payload.map((row) => normalizeBusinessObject(row))
    return { results, count: results.length }
  }

  if (payload?.results && Array.isArray(payload.results)) {
    const results = payload.results.map((row: any) => normalizeBusinessObject(row))
    const count = payload.count || payload.total || results.length
    return { results, count }
  }

  if (payload?.hardcoded || payload?.custom) {
    const hardcoded = Array.isArray(payload.hardcoded) ? payload.hardcoded : []
    const custom = Array.isArray(payload.custom) ? payload.custom : []
    const results = [
      ...hardcoded.map((row: any) => normalizeBusinessObject(row, 'hardcoded')),
      ...custom.map((row: any) => normalizeBusinessObject(row, 'custom'))
    ].filter((row) => !!row.code)
    return { results, count: results.length }
  }

  if (payload?.data && Array.isArray(payload.data)) {
    const results = payload.data.map((row: any) => normalizeBusinessObject(row))
    return { results, count: results.length }
  }

  return { results: [], count: 0 }
}

const columns = computed<TableColumn[]>(() => [
  { prop: 'name', label: t('system.businessObject.columns.name'), minWidth: 180 },
  { prop: 'code', label: t('system.businessObject.columns.code'), width: 160 },
  { prop: 'description', label: t('system.businessObject.columns.description'), minWidth: 220 },
  {
    prop: 'type',
    label: t('system.businessObject.columns.type'),
    width: 110,
    align: 'center',
    tagType: (row: BusinessObject) => (!row.isHardcoded ? 'warning' : 'success'),
    format: (_v: any, row: BusinessObject) =>
      (!row.isHardcoded ? t('system.businessObject.type.custom') : t('system.businessObject.type.system'))
  },
  { prop: 'fieldCount', label: t('system.businessObject.columns.fieldCount'), width: 110, align: 'center' },
  { prop: 'layoutCount', label: t('system.businessObject.columns.layoutCount'), width: 110, align: 'center' },
  {
    prop: 'enableWorkflow',
    label: t('system.businessObject.columns.workflow'),
    width: 110,
    align: 'center',
    tagType: (row: BusinessObject) => (row.enableWorkflow ? 'success' : 'info'),
    format: (_v: any, row: BusinessObject) => (row.enableWorkflow ? t('system.status.enabled') : t('system.status.disabled'))
  },
  { prop: 'actions', label: t('common.table.operations'), width: 220, fixed: 'right', slot: true }
])

const fetchList = async (params: any) => {
  try {
    const res: any = await businessObjectApi.list({
      ...params,
      page_size: params.pageSize
    })

    // request.ts unwraps `{ success, data }` to `data` by default (unwrap=auto).
    // For `/system/business-objects/`, backend returns grouped registry: `{ hardcoded: [], custom: [] }`.
    const payload = res?.data && (res.data.hardcoded || res.data.custom) ? res.data : res

    return resolveListPayload(payload)
  } catch (error) {
    ElMessage.error(t('system.businessObject.messages.loadFailed'))
    return { results: [], count: 0 }
  }
}

const handleRefresh = () => {
  listRef.value?.refresh()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: BusinessObject) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleFields = (row: BusinessObject) => {
  router.push({
    path: '/system/field-definitions',
    query: { objectCode: row.code, objectName: row.name }
  })
}

const handleLayouts = (row: BusinessObject) => {
  router.push({
    path: '/system/page-layouts',
    query: { objectCode: row.code, objectName: row.name }
  })
}
</script>

<style scoped>
.business-object-list {
  padding: 20px;
}
</style>
