<template>
  <div class="supplier-list">
    <!-- Header -->
    <div class="page-header">
      <div class="header-title">
        <span class="title-text">供应商管理</span>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          新建供应商
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
        <el-form-item label="状态">
          <el-select
            v-model="filterForm.isActive"
            clearable
            placeholder="全部状态"
            @change="handleSearch"
          >
            <el-option
              label="启用"
              :value="true"
            />
            <el-option
              label="停用"
              :value="false"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="供应商名称/编码/联系人"
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
          label="供应商编码"
          width="150"
        />
        <el-table-column
          prop="name"
          label="供应商名称"
          width="200"
        />
        <el-table-column
          prop="contactPerson"
          label="联系人"
          width="120"
        />
        <el-table-column
          prop="contactPhone"
          label="联系电话"
          width="140"
        />
        <el-table-column
          prop="email"
          label="邮箱"
          width="180"
        />
        <el-table-column
          prop="address"
          label="地址"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column
          label="状态"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="row.isActive ? 'success' : 'danger'">
              {{ row.isActive ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
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
                查看
              </el-button>
              <el-button
                link
                type="primary"
                @click="handleEdit(row)"
              >
                编辑
              </el-button>
              <el-button
                link
                type="danger"
                @click="handleDelete(row)"
              >
                删除
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
import { getSupplierList, deleteSupplier } from '@/api/assets/suppliers'

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
    await ElMessageBox.confirm(`确定要删除供应商"${row.name}"吗？`, '确认操作', { type: 'warning' })
    await deleteSupplier(row.id)
    ElMessage.success('删除成功')
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
