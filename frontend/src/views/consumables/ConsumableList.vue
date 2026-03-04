<template>
  <div class="consumable-list">
    <BaseListPage
      ref="listRef"
      :title="t('consumables.title')"
      object-code="Consumable"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchConsumables"
    >
      <template #toolbar>
        <el-button
          type="success"
          @click="handleStockIn"
        >
          {{ t('consumables.actions.stockIn') }}
        </el-button>
        <el-button
          type="warning"
          @click="handleStockOut"
        >
          {{ t('consumables.actions.stockOut') }}
        </el-button>
        <el-button
          type="primary"
          @click="handleCreate"
        >
          {{ t('consumables.actions.create') }}
        </el-button>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleEdit(row)"
        >
          {{ t('actions.edit') }}
        </el-button>
        <el-button
          link
          type="primary"
          @click="handleHistory(row)"
        >
          {{ t('consumables.actions.history') }}
        </el-button>
        <el-popconfirm
          :title="t('confirm.delete')"
          @confirm="handleDelete(row)"
        >
          <template #reference>
            <el-button
              link
              type="danger"
            >
              {{ t('actions.delete') }}
            </el-button>
          </template>
        </el-popconfirm>
      </template>
    </BaseListPage>

    <!-- Forms/Dialogs -->
    <ConsumableForm
      v-if="formVisible"
      :id="selectedId"
      v-model="formVisible"
      @success="handleRefresh"
    />
    <StockOperationDialog
      v-if="stockVisible"
      v-model="stockVisible"
      :type="stockType"
      @success="handleRefresh"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { getConsumables, deleteConsumable } from '@/api/consumables'
import { ElMessage } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'
import ConsumableForm from './ConsumableForm.vue'
import StockOperationDialog from './StockOperationDialog.vue'

const { t } = useI18n()

const listRef = ref()

const searchFields = computed<SearchField[]>(() => [
  { prop: 'search', label: t('consumables.fields.nameCode'), type: 'text', placeholder: t('consumables.placeholders.nameCode') },
  { prop: 'category', label: t('consumables.fields.category'), type: 'select', options: [
    { label: t('consumables.categories.office'), value: 'office' },
    { label: t('consumables.categories.it'), value: 'it' }
  ]}
])

const columns = computed<TableColumn[]>(() => [
  { prop: 'code', label: t('consumables.fields.code'), width: 120 },
  { prop: 'name', label: t('consumables.fields.name'), width: 150 },
  { prop: 'category', label: t('consumables.fields.category'), width: 100 },
  { prop: 'spec', label: t('consumables.fields.spec'), width: 150 },
  { prop: 'stockQuantity', label: t('consumables.fields.stockQuantity'), width: 120,
    tagType: (row: any) => getStockStatusType(row),
    format: (_value: any, row: any) => `${row?.stockQuantity ?? row?.stock_quantity ?? '-'} ${row?.unit || ''}`.trim()
  },
  { prop: 'actions', label: t('labels.operation'), width: 180, slot: true, fixed: 'right' }
])

const formVisible = ref(false)
const selectedId = ref<number | undefined>(undefined)

const stockVisible = ref(false)
const stockType = ref<'in' | 'out'>('in')

const fetchConsumables = async (params: any) => {
  const res = await getConsumables({
    ...params,
    page_size: params.pageSize
  })
  return {
    results: (res as any).results || (res as any).items || [],
    count: (res as any).count || (res as any).total || 0
  }
}

const handleRefresh = () => {
  listRef.value?.refresh()
}

const handleCreate = () => {
    selectedId.value = undefined
    formVisible.value = true
}

const handleEdit = (row: any) => {
    selectedId.value = row.id
    formVisible.value = true
}

const handleDelete = async (row: any) => {
    try {
        await deleteConsumable(row.id)
        ElMessage.success(t('success.delete'))
        handleRefresh()
    } catch (e) {
        ElMessage.error(t('errors.deleteFailed'))
    }
}

const handleStockIn = () => {
    stockType.value = 'in'
    stockVisible.value = true
}

const handleStockOut = () => {
    stockType.value = 'out'
    stockVisible.value = true
}

const handleHistory = (_row: any) => {
    // Navigate to history or show dialog (TODO)
    ElMessage.info(t('messages.comingSoon'))
}

const getStockStatusType = (row: any) => {
    const quantity = row.stockQuantity ?? row.stock_quantity ?? 0
    const warning = row.warningQuantity ?? row.warning_quantity ?? 0
    if (quantity <= warning) return 'danger'
    return 'success'
}
</script>

<style scoped>
.consumable-list { padding: 20px; }
</style>
