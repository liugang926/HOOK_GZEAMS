<template>
  <div class="dictionary-type-list">
    <div class="page-header">
      <h3>数据字典管理</h3>
      <el-button type="primary" @click="handleCreate">新建字典类型</el-button>
    </div>

    <!-- Filters -->
    <el-form :model="filterForm" inline class="filter-form">
      <el-form-item label="状态">
        <el-select v-model="filterForm.is_active" clearable placeholder="全部" @change="handleSearch">
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
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
      <el-table-column prop="code" label="字典编码" width="180" />
      <el-table-column prop="name" label="字典名称" width="180" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="系统字典" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_system ? 'danger' : 'success'" size="small">
            {{ row.is_system ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="item_count" label="字典项数量" width="110" align="center">
        <template #default="{ row }">
          <el-link type="primary" @click="handleViewItems(row)">
            {{ row.item_count || 0 }} 项
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="80" align="center" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleViewItems(row)">字典项</el-button>
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button
            v-if="!row.is_system"
            link
            type="danger"
            @click="handleDelete(row)"
          >
            删除
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
    ElMessage.error('加载数据失败')
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
      `确定删除字典类型"${row.name}"吗？删除后关联的字典项也将被删除。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )

    await dictionaryTypeApi.delete(row.id)
    ElMessage.success('删除成功')
    await fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
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
