<template>
  <div class="loan-list page-container">
    <BaseListPage
      ref="listRef"
      title="资产借出单"
      object-code="asset_loan_list"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchLoanList"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          新建借出单
        </el-button>
      </template>

      <template #status="{ row }">
        <el-tag
          :type="getStatusType(row.status)"
          class="status-tag"
          :class="`status-${row.status}`"
        >
          {{ row.statusLabel || getStatusLabel(row.status) }}
        </el-tag>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleView(row)"
        >
          查看
        </el-button>
        <el-button
          v-if="['draft', 'pending'].includes(row.status)"
          link
          type="primary"
          @click="handleEdit(row)"
        >
          编辑
        </el-button>
        <el-button
          v-if="['draft', 'pending'].includes(row.status)"
          link
          type="warning"
          @click="handleCancel(row)"
        >
          取消
        </el-button>
        <el-button
          v-if="row.status === 'loaned'"
          link
          type="success"
          @click="handleReturn(row)"
        >
          归还
        </el-button>
      </template>
    </BaseListPage>

    <!-- Return Dialog -->
    <el-dialog
      v-model="returnDialogVisible"
      title="资产归还"
      width="600px"
    >
      <el-form
        :model="returnForm"
        label-width="120px"
      >
        <el-form-item label="归还日期">
          <el-date-picker
            v-model="returnForm.returnDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="请选择归还日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="归还说明">
          <el-input
            v-model="returnForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入归还说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="returnDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="confirmReturn"
        >
          确认归还
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getLoanList, cancelLoan, returnLoan } from '@/api/assets/loans'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()
const listRef = ref()
const returnDialogVisible = ref(false)
const currentLoan = ref<any>(null)

const returnForm = reactive({
  returnDate: new Date().toISOString().split('T')[0],
  remark: ''
})

const fetchLoanList = async (params: any) => {
  const apiParams = {
    ...params,
    page_size: params.pageSize
  }
  const res = await getLoanList(apiParams)
  return {
    results: res.items || res.results || [],
    count: res.total || res.count || 0
  }
}

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '草稿', value: 'draft' },
      { label: '待审批', value: 'pending' },
      { label: '已批准', value: 'approved' },
      { label: '借出中', value: 'loaned' },
      { label: '已归还', value: 'returned' },
      { label: '已拒绝', value: 'rejected' },
      { label: '已取消', value: 'cancelled' }
    ]
  },
  {
    prop: 'search',
    label: '搜索',
    type: 'text',
    placeholder: '借出单号/借用人'
  }
]

const columns: TableColumn[] = [
  { prop: 'loanNo', label: '借出单号', width: 150 },
  { prop: 'borrower.realName', label: '借用人', width: 100 },
  { prop: 'borrower.department.name', label: '部门', width: 120 },
  { prop: 'loanDate', label: '借出日期', width: 110 },
  { prop: 'expectedReturnDate', label: '预计归还日期', width: 120 },
  { prop: 'actualReturnDate', label: '实际归还日期', width: 120 },
  { prop: 'status', label: '状态', width: 100, slot: 'status' },
  { prop: 'itemsCount', label: '资产数量', width: 100, align: 'center' }
]

const getStatusType = (status: string) => {
  const map: any = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    loaned: 'primary',
    returned: '',
    rejected: 'danger',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: any = {
    draft: '草稿',
    pending: '待审批',
    approved: '已批准',
    loaned: '借出中',
    returned: '已归还',
    rejected: '已拒绝',
    cancelled: '已取消'
  }
  return map[status] || status
}

const handleCreate = () => {
  router.push('/assets/operations/loans/create')
}

const handleView = (row: any) => {
  router.push(`/assets/operations/loans/${row.id}`)
}

const handleEdit = (row: any) => {
  router.push(`/assets/operations/loans/${row.id}/edit`)
}

const handleCancel = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要取消此借出单吗？', '确认操作', { type: 'warning' })
    await cancelLoan(row.id)
    ElMessage.success('已取消')
    listRef.value?.refresh()
  } catch {
    // cancelled
  }
}

const handleReturn = (row: any) => {
  currentLoan.value = row
  returnForm.returnDate = new Date().toISOString().split('T')[0]
  returnForm.remark = ''
  returnDialogVisible.value = true
}

const confirmReturn = async () => {
  try {
    await returnLoan(currentLoan.value.id, {
      return_date: returnForm.returnDate,
      remark: returnForm.remark
    })
    ElMessage.success('归还成功')
    returnDialogVisible.value = false
    listRef.value?.refresh()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '归还失败')
  }
}
</script>

<style scoped lang="scss">
.loan-list {
  // Global styles applied via page-container
}
</style>
