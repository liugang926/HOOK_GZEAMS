<template>
  <div class="dictionary-type-list">
    <div class="page-header">
      <h3>{{ $t('system.dictionary.title') }}</h3>
      <el-button
        type="primary"
        @click="handleCreate"
      >
        {{ $t('system.dictionary.createTypButton') }}
      </el-button>
    </div>

    <!-- Filters -->
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item :label="$t('system.department.columns.status')">
        <el-select
          v-model="filterForm.is_active"
          clearable
          :placeholder="$t('system.common.all')"
          @change="handleSearch"
        >
          <el-option
            :label="$t('system.dictionary.status.enabled')"
            :value="true"
          />
          <el-option
            :label="$t('system.dictionary.status.disabled')"
            :value="false"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          @click="handleSearch"
        >
          {{ $t('common.actions.search') }}
        </el-button>
        <el-button @click="handleReset">
          {{ $t('common.actions.reset') }}
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Dictionary Types Table -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column
        prop="code"
        :label="$t('system.dictionary.columns.code')"
        width="180"
      />
      <el-table-column
        prop="name"
        :label="$t('system.dictionary.columns.name')"
        width="180"
      />
      <el-table-column
        prop="description"
        :label="$t('system.dictionary.columns.description')"
        min-width="200"
        show-overflow-tooltip
      />
      <el-table-column
        :label="$t('system.dictionary.columns.isSystem')"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.is_system ? 'danger' : 'success'"
            size="small"
          >
            {{ row.is_system ? $t('system.dictionary.isSystem.yes') : $t('system.dictionary.isSystem.no') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('system.dictionary.columns.status')"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.is_active ? 'success' : 'info'"
            size="small"
          >
            {{ row.is_active ? $t('system.dictionary.status.enabled') : $t('system.dictionary.status.disabled') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="item_count"
        :label="$t('system.dictionary.columns.itemCount')"
        width="110"
        align="center"
      >
        <template #default="{ row }">
          <el-link
            type="primary"
            @click="handleViewItems(row)"
          >
            {{ row.item_count || 0 }} {{ $t('system.common.item') }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column
        prop="sort_order"
        :label="$t('system.dictionary.columns.sortOrder')"
        width="80"
        align="center"
      />
      <el-table-column
        :label="$t('common.labels.operation')"
        width="200"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleViewItems(row)"
          >
            {{ $t('system.dictionary.actions.viewItems') }}
          </el-button>
          <el-button
            link
            type="primary"
            @click="handleEdit(row)"
          >
            {{ $t('common.actions.edit') }}
          </el-button>
          <el-button
            v-if="!row.is_system"
            link
            type="danger"
            @click="handleDelete(row)"
          >
            {{ $t('common.actions.delete') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-footer">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>

    <!-- Dictionary Type Form Dialog -->
    <DictionaryTypeForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="fetchData"
    />

    <!-- Dictionary Items Dialog -->
    <DictionaryItemsDialog
      v-model:visible="itemsDialogVisible"
      :dictionary-type="selectedType"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { DictionaryType } from '@/api/system'
import { dictionaryTypeApi } from '@/api/system'
import DictionaryTypeForm from './components/DictionaryTypeForm.vue'
import DictionaryItemsDialog from './components/DictionaryItemsDialog.vue'

const loading = ref(false)
const tableData = ref<DictionaryType[]>([])
const dialogVisible = ref(false)
const itemsDialogVisible = ref(false)
const currentRow = ref<DictionaryType | null>(null)
const selectedType = ref<DictionaryType | null>(null)
const { t } = useI18n()

const filterForm = reactive({
  is_active: undefined as unknown as boolean
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await dictionaryTypeApi.list({
      ...filterForm,
      page: pagination.page,
      page_size: pagination.pageSize
    }) as any

    tableData.value = res.results || []
    pagination.total = res.count || 0
  } catch (error) {
    ElMessage.error(t('system.dictionary.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  filterForm.is_active = undefined as unknown as boolean
  handleSearch()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: DictionaryType) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleViewItems = (row: DictionaryType) => {
  selectedType.value = row
  itemsDialogVisible.value = true
}

const handleDelete = async (row: DictionaryType) => {
  try {
    await ElMessageBox.confirm(
      t('system.dictionary.messages.confirmDelete', { name: row.name }),
      t('system.dictionary.messages.confirmDeleteTitle'),
      {
        type: 'warning',
        confirmButtonText: t('common.actions.confirm'),
        cancelButtonText: t('common.actions.cancel')
      }
    )

    await dictionaryTypeApi.delete(row.id)
    ElMessage.success(t('common.messages.deleteSuccess'))
    await fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(t('common.messages.deleteFailed'))
    }
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.dictionary-type-list {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h3 {
  margin: 0;
  font-size: 18px;
}
.filter-form {
  margin-bottom: 20px;
}
.pagination-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
