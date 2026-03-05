<template>
  <el-dialog
    v-model="visible"
    :title="t('assets.selector.selectAsset')"
    width="800px"
    @open="handleOpen"
  >
    <el-form
      :model="filterForm"
      inline
    >
      <el-form-item :label="t('assets.search.keyword')">
        <el-input
          v-model="filterForm.search"
          :placeholder="t('assets.search.keywordPlaceholder')"
          clearable
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item :label="t('assets.fields.category')">
        <el-tree-select
          v-model="filterForm.categoryId"
          :data="categoryTree"
          :props="{ value: 'id', label: 'name', children: 'children' }"
          :placeholder="t('assets.fields.category')"
          clearable
          check-strictly
          style="width: 200px"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          @click="handleSearch"
        >
          {{ t('common.actions.search') }}
        </el-button>
        <el-button @click="resetFilter">
          {{ t('common.actions.reset') }}
        </el-button>
      </el-form-item>
    </el-form>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      height="400"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        type="selection"
        width="55"
      />
      <el-table-column
        prop="code"
        :label="t('assets.fields.assetCode')"
        width="140"
      />
      <el-table-column
        prop="name"
        :label="t('assets.fields.assetName')"
        min-width="150"
      />
      <el-table-column
        prop="categoryName"
        :label="t('assets.fields.category')"
        width="120"
      />
      <el-table-column
        prop="specification"
        :label="t('assets.lifecycle.purchaseRequest.form.specification')"
        width="120"
        show-overflow-tooltip
      />
      <el-table-column
        prop="status"
        :label="t('assets.search.status')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchData"
      />
    </div>

    <template #footer>
      <el-button @click="visible = false">
        {{ t('common.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :disabled="selectedRows.length === 0"
        @click="confirmSelect"
      >
        {{ t('assets.list.selected', { count: selectedRows.length }) }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { assetApi, categoryApi } from '@/api/assets'
import type { Asset } from '@/types/assets'

const { t } = useI18n()

const props = defineProps({
  modelValue: Boolean,
  statusFilter: {
    type: Array as () => string[],
    default: () => []
  },
  excludeAssetIds: {
    type: Array as () => (string | number)[],
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const tableData = ref<Asset[]>([])
const categoryTree = ref<any[]>([])
const selectedRows = ref<Asset[]>([])

const filterForm = reactive({
  search: '',
  categoryId: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const handleOpen = async () => {
  await loadCategories()
  fetchData()
}

const loadCategories = async () => {
  try {
    const data = await categoryApi.tree()
    categoryTree.value = buildTree(data)
  } catch (e) {
    console.error(e)
  }
}

const buildTree = (items: any[], parentId: string | null = null): any[] => {
  return items
    .filter(item => item.parentId === parentId)
    .map(item => ({
      ...item,
      children: buildTree(items, item.id)
    }))
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      search: filterForm.search,
      categoryId: filterForm.categoryId,
      status: props.statusFilter.join(',')
    }
    const res = await assetApi.list(params)
    tableData.value = res.results || []
    pagination.total = res.count || 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const resetFilter = () => {
  filterForm.search = ''
  filterForm.categoryId = ''
  handleSearch()
}

const handleSelectionChange = (rows: Asset[]) => {
  selectedRows.value = rows
}

const confirmSelect = () => {
  emit('confirm', selectedRows.value)
  visible.value = false
  selectedRows.value = []
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    idle: 'success',
    in_use: 'warning',
    maintenance: 'danger'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    draft: t('assets.status.draft'),
    idle: t('assets.status.idle'),
    in_use: t('assets.status.inUse'),
    maintenance: t('assets.status.maintenance')
  }
  return map[status] || status
}
</script>

<style scoped>
.pagination-container {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}
</style>
