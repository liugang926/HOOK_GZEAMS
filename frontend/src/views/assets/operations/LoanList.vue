<template>
  <div class="loan-list page-container">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.loan.title')"
      object-code="AssetLoan"
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
          {{ $t('assets.loan.createButton') }}
        </el-button>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleView(row)"
        >
          {{ $t('common.actions.view') }}
        </el-button>
        <el-button
          v-if="['draft', 'pending'].includes(row.status)"
          link
          type="primary"
          @click="handleEdit(row)"
        >
          {{ $t('common.actions.edit') }}
        </el-button>
        <el-button
          v-if="['draft', 'pending'].includes(row.status)"
          link
          type="warning"
          @click="handleCancel(row)"
        >
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          v-if="row.status === 'loaned'"
          link
          type="success"
          @click="handleReturn(row)"
        >
          {{ $t('assets.operations.return') }}
        </el-button>
      </template>
    </BaseListPage>

    <!-- Return Dialog -->
    <el-dialog
      v-model="returnDialogVisible"
      :title="$t('assets.loan.dialog.returnTitle')"
      width="600px"
    >
      <el-form
        :model="returnForm"
        :label="$t('assets.loan.dialog.returnDate')"
        label-width="120px"
      >
        <el-form-item :label="$t('assets.loan.dialog.returnDate')">
          <el-date-picker
            v-model="returnForm.returnDate"
            type="date"
            value-format="YYYY-MM-DD"
            :placeholder="$t('assets.loan.dialog.returnDatePlaceholder')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="$t('assets.loan.dialog.returnRemark')">
          <el-input
            v-model="returnForm.remark"
            type="textarea"
            :rows="3"
            :placeholder="$t('assets.loan.dialog.returnRemarkPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="returnDialogVisible = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          @click="confirmReturn"
        >
          {{ $t('assets.loan.dialog.confirmReturn') }}
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
import { useI18n } from 'vue-i18n'
import { getLoanList, cancelLoan, returnLoan } from '@/api/assets/loans'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()
const { t } = useI18n()
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
  const res = await getLoanList(apiParams) as any
  return {
    results: res.items || res.results || [],
    count: res.total || res.count || 0
  }
}

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: t('assets.search.status'),
    type: 'select',
    options: [
      { label: t('assets.status.draft'), value: 'draft' },
      { label: t('assets.status.pending'), value: 'pending' },
      { label: t('assets.status.approved'), value: 'approved' },
      { label: t('assets.status.loaned'), value: 'loaned' },
      { label: t('assets.status.returned'), value: 'returned' },
      { label: t('assets.status.rejected'), value: 'rejected' },
      { label: t('assets.status.cancelled'), value: 'cancelled' }
    ]
  },
  {
    prop: 'search',
    label: t('common.actions.search'),
    type: 'text',
    placeholder: t('assets.search.keywordPlaceholder')
  }
]

const columns: TableColumn[] = [
  { prop: 'loanNo', label: t('assets.loan.columns.loanNo'), width: 150 },
  { prop: 'borrower.realName', label: t('assets.loan.columns.borrower'), width: 100 },
  { prop: 'borrower.department.name', label: t('assets.loan.columns.department'), width: 120 },
  { prop: 'loanDate', label: t('assets.loan.columns.loanDate'), width: 110 },
  { prop: 'expectedReturnDate', label: t('assets.loan.columns.expectedReturnDate'), width: 120 },
  { prop: 'actualReturnDate', label: t('assets.loan.columns.actualReturnDate'), width: 120 },
  { prop: 'status', label: t('assets.loan.columns.status'), width: 100, tagType: (row: any) => getStatusType(row.status), format: (value: any, row: any) => row?.statusLabel || getStatusLabel(value) },
  { prop: 'itemsCount', label: t('assets.loan.columns.assetCount'), width: 100, align: 'center' }
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
    draft: t('assets.status.draft'),
    pending: t('assets.status.pending'),
    approved: t('assets.status.approved'),
    loaned: t('assets.status.loaned'),
    returned: t('assets.status.returned'),
    rejected: t('assets.status.rejected'),
    cancelled: t('assets.status.cancelled')
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
    await ElMessageBox.confirm(t('assets.loan.messages.confirmCancel'), t('common.messages.confirmTitle'), { type: 'warning' })
    await cancelLoan(row.id)
    ElMessage.success(t('common.messages.cancelSuccess'))
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
    ElMessage.success(t('assets.loan.messages.returnSuccess'))
    returnDialogVisible.value = false
    listRef.value?.refresh()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || t('assets.loan.messages.returnFailed'))
  }
}
</script>

<style scoped lang="scss">
.loan-list {
  // Global styles applied via page-container
}
</style>
