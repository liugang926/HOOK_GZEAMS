<template>
  <div class="supplier-list">
    <!-- Header -->
    <div class="page-header">
      <div class="header-title">
        <span class="title-text">{{ t('assets.supplier.manage') }}</span>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          {{ t('assets.supplier.create') }}
        </el-button>
      </div>
    </div>

    <!-- Filters -->
    <el-card
      class="filter-card"
      shadow="never"
    >
      <el-form
        :model="filterForm"
        inline
      >
        <el-form-item :label="t('common.labels.status')">
          <el-select
            v-model="filterForm.isActive"
            clearable
            :placeholder="t('common.filters.all')"
            @change="handleSearch"
          >
            <el-option
              :label="t('common.status.enabled')"
              :value="true"
            />
            <el-option
              :label="t('common.status.inactive')"
              :value="false"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('common.actions.search')">
          <el-input
            v-model="filterForm.search"
            :placeholder="`${t('assets.supplier.name')}/${t('assets.supplier.code')}/${t('assets.supplier.contact')}`"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button
                :icon="Search"
                @click="handleSearch"
              />
            </template>
          </el-input>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table -->
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="tableData"
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column
          prop="code"
          :label="t('assets.supplier.code')"
          width="150"
        />
        <el-table-column
          prop="name"
          :label="t('assets.supplier.name')"
          width="200"
        />
        <el-table-column
          prop="contactPerson"
          :label="t('assets.supplier.contact')"
          width="120"
        />
        <el-table-column
          prop="contactPhone"
          :label="t('assets.supplier.phone')"
          width="140"
        />
        <el-table-column
          prop="email"
          :label="t('assets.supplier.email')"
          width="180"
        />
        <el-table-column
          prop="address"
          :label="t('assets.supplier.address')"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column
          :label="t('common.labels.status')"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="row.isActive ? 'success' : 'danger'">
              {{ row.isActive ? t('common.status.enabled') : t('common.status.inactive') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          :label="t('common.table.operations')"
          width="180"
          fixed="right"
        >
          <template #default="{ row }">
            <div @click.stop>
              <el-button
                link
                type="primary"
                @click="handleView(row)"
              >
                {{ t('common.actions.view') }}
              </el-button>
              <el-button
                link
                type="primary"
                @click="handleEdit(row)"
              >
                {{ t('common.actions.edit') }}
              </el-button>
              <el-button
                link
                type="danger"
                @click="handleDelete(row)"
              >
                {{ t('common.actions.delete') }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-footer">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { getSupplierList, deleteSupplier } from '@/api/assets/suppliers'

const { t } = useI18n()

const router = useRouter()
const loading = ref(false)
const tableData = ref([])

const filterForm = reactive({
  isActive: '',
  search: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getSupplierList({
      ...filterForm,
      page: pagination.page,
      page_size: pagination.page_size
    })
    tableData.value = res.results || res.items || []
    pagination.total = res.count || res.total || 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleCreate = () => {
  router.push('/assets/settings/suppliers/create')
}

const handleView = (row: any) => {
  router.push(`/assets/settings/suppliers/${row.id}`)
}

const handleEdit = (row: any) => {
  router.push(`/assets/settings/suppliers/${row.id}/edit`)
}

const handleRowClick = (row: any) => {
  handleView(row)
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`${t('common.dialog.confirmDeleteMessage').replace('{count}', `"${row.name}"`)}`, t('common.dialog.confirmTitle'), { type: 'warning' })
    await deleteSupplier(row.id)
    ElMessage.success(t('common.messages.deleteSuccess'))
    fetchData()
  } catch {
    // cancelled
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.supplier-list {
    padding: 20px;
}
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.title-text {
    font-size: 20px;
    font-weight: 500;
}
.filter-card {
    margin-bottom: 20px;
}
.pagination-footer {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
}
</style>
