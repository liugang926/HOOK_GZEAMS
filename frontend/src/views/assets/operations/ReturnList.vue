<template>
  <div class="return-list">
    <!-- Header -->
    <div class="page-header">
      <div class="header-title">
        <span class="title-text">资产退库单</span>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          新建退库单
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
            v-model="filterForm.status"
            clearable
            placeholder="全部状态"
            @change="handleSearch"
          >
            <el-option
              label="待审批"
              value="pending"
            />
            <el-option
              label="已批准"
              value="approved"
            />
            <el-option
              label="已拒绝"
              value="rejected"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="资产名称/单号"
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
      >
        <el-table-column
          prop="return_no"
          label="退库单号"
          width="150"
        />
        <el-table-column
          prop="asset.name"
          label="资产名称"
          width="120"
        />
        <el-table-column
          prop="return_date"
          label="退库日期"
          width="110"
        />
        <el-table-column
          prop="applicant.real_name"
          label="退库人"
          width="100"
        />
        <el-table-column
          prop="created_at"
          label="申请时间"
          width="160"
        />
        <el-table-column
          label="状态"
          width="100"
        >
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="200"
          fixed="right"
        >
          <template #default="{ row }">
            <div v-if="row.status === 'pending'">
              <el-button
                link
                type="success"
                @click="handleApprove(row)"
              >
                批准
              </el-button>
              <el-button
                link
                type="danger"
                @click="handleReject(row)"
              >
                拒绝
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-footer">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
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
import { returnApi } from '@/api/assets/return'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])

const filterForm = reactive({
  status: '',
  search: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getStatusType = (status: string) => {
  const map: any = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: any = { pending: '待审批', approved: '已批准', rejected: '已拒绝' }
  return map[status] || status
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await returnApi.list({
      ...filterForm,
      page: pagination.page,
      pageSize: pagination.pageSize
    })
    tableData.value = res.items || res.results || []
    pagination.total = res.total || res.count || 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
    pagination.page = 1
    fetchData()
}

const handleCreate = () => {
    router.push('/assets/operations/return/create')
}

const handleApprove = async (row: any) => {
    try {
        await ElMessageBox.confirm('确定批准此退库申请吗？', '提示', { type: 'success' })
        await returnApi.approve(row.id)
        ElMessage.success('已批准')
        fetchData()
    } catch {}
}

const handleReject = async (row: any) => {
    try {
        const { value } = await ElMessageBox.prompt('请输入拒绝理由', '拒绝申请', {
            inputPattern: /\S+/,
            inputErrorMessage: '理由不能为空'
        })
        await returnApi.reject(row.id, value)
        ElMessage.success('已拒绝')
        fetchData()
    } catch {}
}

onMounted(() => {
    fetchData()
})
</script>

<style scoped>
.return-list { padding: 20px; }
.page-header { display: flex; justify-content: space-between; margin-bottom: 20px; }
.title-text { font-size: 20px; font-weight: 500; }
.pagination-footer { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>
