<template>
  <el-dialog
    v-model="visible"
    :title="t('assets.selector.selectAsset')"
    width="860px"
    destroy-on-close
    @open="handleOpen"
  >
    <el-form
      :model="filterForm"
      inline
      class="selector-filter-form"
    >
      <el-form-item :label="t('assets.search.keyword')">
        <el-input
          v-model="filterForm.search"
          :placeholder="t('assets.search.keywordPlaceholder')"
          clearable
          @input="handleSearchDebounced"
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
          @change="handleSearch"
        />
      </el-form-item>
      <el-form-item
        v-if="showDepartmentFilter"
        :label="t('assets.search.department')"
      >
        <DeptPicker
          v-model="filterForm.departmentId"
          :placeholder="t('assets.search.departmentPlaceholder')"
          style="width: 200px"
          @change="handleSearch"
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
      :data="filteredTableData"
      border
      height="400"
      row-key="id"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        type="selection"
        width="55"
        :selectable="isRowSelectable"
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
        :label="t('assets.search.location')"
        width="120"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          {{ row.location?.name || row.locationName || '—' }}
        </template>
      </el-table-column>
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
import DeptPicker from '@/components/common/DeptPicker.vue'
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
  },
  departmentId: {
    type: String,
    default: ''
  },
  showDepartmentFilter: {
    type: Boolean,
    default: false
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
  categoryId: '',
  departmentId: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// Debounced search — triggers after 300ms if ≥2 chars
let searchTimer: ReturnType<typeof setTimeout> | null = null
const handleSearchDebounced = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    if (filterForm.search.length >= 2 || filterForm.search.length === 0) {
      handleSearch()
    }
  }, 300)
}

// Filter out already-selected assets from table display
const filteredTableData = computed(() => {
  if (props.excludeAssetIds.length === 0) return tableData.value
  const excludeSet = new Set(props.excludeAssetIds.map(String))
  return tableData.value.filter(item => !excludeSet.has(String(item.id)))
})

const isRowSelectable = (row: Asset) => {
  return !props.excludeAssetIds.map(String).includes(String(row.id))
}

const handleOpen = async () => {
  // Pre-fill department filter if passed
  if (props.departmentId) {
    filterForm.departmentId = props.departmentId
  }
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
    const params: Record<string, any> = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      search: filterForm.search || undefined,
      categoryId: filterForm.categoryId || undefined,
      status: props.statusFilter.length > 0 ? props.statusFilter.join(',') : undefined,
      departmentId: filterForm.departmentId || undefined
    }
    // Clean undefined params
    Object.keys(params).forEach(key => {
      if (params[key] === undefined) delete params[key]
    })
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
  filterForm.departmentId = ''
  handleSearch()
}

const handleSelectionChange = (rows: Asset[]) => {
  selectedRows.value = rows
}

const confirmSelect = () => {
  // Emit full asset objects for auto-fill (location, custodian, etc.)
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

<style scoped lang="scss">
.selector-filter-form {
  margin-bottom: 12px;
}

.pagination-container {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}
</style>
