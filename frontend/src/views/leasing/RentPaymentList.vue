<!-- Rent Payment List: track and confirm rent payments -->
<template>
  <div class="page-container">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.leasing.payment.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchList"
    >
      <template #status="{ row }">
        <el-tag
          :type="getStatusType(row.status)"
          size="small"
        >
          {{ getStatusLabel(row.status) }}
        </el-tag>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="$router.push(`/objects/RentPayment/${row.id}`)"
        >
          {{ $t('common.actions.view') }}
        </el-button>
        <el-button
          v-if="row.status === 'pending'"
          link
          type="success"
          @click="handleConfirmPayment(row)"
        >
          {{ $t('assets.leasing.payment.actions.confirm') }}
        </el-button>
      </template>
    </BaseListPage>

    <!-- Confirm payment dialog -->
    <el-dialog
      v-model="confirmDialog"
      :title="$t('assets.leasing.payment.dialog.confirmTitle')"
      width="480px"
      destroy-on-close
    >
      <el-form
        :model="confirmForm"
        label-width="120px"
      >
        <el-form-item :label="$t('assets.leasing.payment.form.actualAmount')">
          <el-input-number
            v-model="confirmForm.actualAmount"
            :min="0"
            :precision="2"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item :label="$t('assets.leasing.payment.form.paymentDate')">
          <el-date-picker
            v-model="confirmForm.paymentDate"
            type="date"
            style="width:100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item :label="$t('assets.leasing.payment.form.paymentMethod')">
          <el-select
            v-model="confirmForm.paymentMethod"
            style="width:100%"
          >
            <el-option
              label="閾惰杞处"
              value="bank_transfer"
            />
            <el-option
              label="鏀エ"
              value="check"
            />
            <el-option
              label="鐜伴噾"
              value="cash"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('assets.leasing.payment.form.remark')">
          <el-input
            v-model="confirmForm.remark"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="confirmDialog = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          @click="submitConfirm"
        >
          {{ $t('common.actions.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { rentPaymentApi } from '@/api/leasing'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'

const { t } = useI18n()
const listRef = ref()

const fetchList = async (params: any) => {
  const res = await rentPaymentApi.list({ ...params, page_size: params.pageSize }) as any
  return { results: res?.results ?? res?.data?.results ?? [], count: res?.count ?? res?.data?.count ?? 0 }
}

const statuses = ['pending', 'paid', 'overdue', 'partial']

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: t('assets.leasing.payment.columns.status'),
    type: 'select',
    options: statuses.map(s => ({ label: t(`assets.leasing.payment.status.${s}`), value: s }))
  },
  { prop: 'search', label: t('common.actions.search'), type: 'text'}
]

const columns: TableColumn[] = [
  { prop: 'contractDisplay', label: t('assets.leasing.payment.columns.contract'), width: 160 },
  { prop: 'dueDate', label: t('assets.leasing.payment.columns.dueDate'), width: 120 },
  { prop: 'amount', label: t('assets.leasing.payment.columns.amount'), width: 120, align: 'right' },
  { prop: 'period', label: t('assets.leasing.payment.columns.period'), width: 120 },
  { prop: 'status', label: t('assets.leasing.payment.columns.status'), width: 100, slot: 'status' }
]

const getStatusType = (s: string) => {
  const map: Record<string, string> = { pending: 'warning', paid: 'success', overdue: 'danger', partial: 'info' }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.leasing.payment.status.${s}`) || s

const confirmDialog = ref(false)
const confirmForm = reactive({ id: '', actualAmount: 0, paymentDate: '', paymentMethod: 'bank_transfer', remark: '' })

const handleConfirmPayment = (row: any) => {
  confirmForm.id = row.id
  confirmForm.actualAmount = row.amount || 0
  confirmForm.paymentDate = ''
  confirmForm.remark = ''
  confirmDialog.value = true
}

const submitConfirm = async () => {
  try {
    await rentPaymentApi.confirm(confirmForm.id, {
      actual_amount: confirmForm.actualAmount,
      payment_date: confirmForm.paymentDate,
      payment_method: confirmForm.paymentMethod,
      remark: confirmForm.remark
    })
    ElMessage.success(t('assets.leasing.payment.messages.confirmSuccess'))
    confirmDialog.value = false
    listRef.value?.refresh()
  } catch (e: any) { ElMessage.error(e?.message) }
}
</script>

