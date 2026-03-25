<!-- Claim Record List: dedicated claim management with workflow status -->
<template>
  <div class="page-container">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.insurance.claim.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchList"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="$router.push('/insurance/claims/create')"
        >
          {{ $t('assets.insurance.claim.createButton') }}
        </el-button>
      </template>

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
          @click="$router.push(`/objects/ClaimRecord/${row.id}`)"
        >
          {{ $t('common.actions.view') }}
        </el-button>
        <el-button
          v-if="row.status === 'draft'"
          link
          type="warning"
          @click="handleSubmit(row)"
        >
          {{ $t('assets.insurance.claim.actions.submit') }}
        </el-button>
        <el-button
          v-if="row.status === 'reported'"
          link
          type="success"
          @click="handleApprove(row)"
        >
          {{ $t('assets.insurance.claim.actions.approve') }}
        </el-button>
      </template>
    </BaseListPage>

    <!-- Approve dialog -->
    <el-dialog
      v-model="approveDialog"
      :title="$t('assets.insurance.claim.dialog.approveTitle')"
      width="480px"
      destroy-on-close
    >
      <el-form
        :model="approveForm"
        label-width="120px"
      >
        <el-form-item :label="$t('assets.insurance.claim.form.approvedAmount')">
          <el-input-number
            v-model="approveForm.approvedAmount"
            :min="0"
            :precision="2"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item :label="$t('assets.insurance.claim.form.approveComment')">
          <el-input
            v-model="approveForm.comment"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveDialog = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          @click="confirmApprove"
        >
          {{ $t('common.actions.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { claimRecordApi } from '@/api/insurance'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'

const { t } = useI18n()
const listRef = ref()

const fetchList = async (params: any) => {
  const res = await claimRecordApi.list({ ...params, page_size: params.pageSize }) as any
  return { results: res?.results ?? res?.data?.results ?? [], count: res?.count ?? res?.data?.count ?? 0 }
}

const statuses = ['draft', 'reported', 'under_review', 'approved', 'rejected', 'paid']

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: t('assets.insurance.claim.columns.status'),
    type: 'select',
    options: statuses.map(s => ({ label: t(`assets.insurance.claim.status.${s}`), value: s }))
  },
  { prop: 'search', label: t('common.actions.search'), type: 'text',
    placeholder: t('assets.insurance.claim.columns.claimNo') }
]

const columns: TableColumn[] = [
  { prop: 'claimNo', label: t('assets.insurance.claim.columns.claimNo'), width: 160 },
  { prop: 'policyDisplay', label: t('assets.insurance.claim.columns.policy'), width: 140 },
  { prop: 'incidentDate', label: t('assets.insurance.claim.columns.incidentDate'), width: 120 },
  { prop: 'claimAmount', label: t('assets.insurance.claim.columns.claimAmount'), width: 120, align: 'right' },
  { prop: 'approvedAmount', label: t('assets.insurance.claim.columns.approvedAmount'), width: 120, align: 'right' },
  { prop: 'status', label: t('assets.insurance.claim.columns.status'), width: 110, slot: 'status' }
]

const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    draft: 'info', reported: 'warning', under_review: 'primary',
    approved: 'success', rejected: 'danger', paid: ''
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.insurance.claim.status.${s}`) || s

const approveDialog = ref(false)
const approveForm = reactive({ approvedAmount: 0, comment: '', id: '' })

const handleSubmit = async (row: any) => {
  try {
    await ElMessageBox.confirm(t('assets.insurance.claim.messages.submitConfirm'), t('common.messages.confirmTitle'), { type: 'info' })
    await claimRecordApi.submit(row.id)
    ElMessage.success(t('assets.insurance.claim.messages.submitSuccess'))
    listRef.value?.refresh()
  } catch { /* cancelled */ }
}

const handleApprove = (row: any) => {
  approveForm.id = row.id
  approveForm.approvedAmount = row.claimAmount || 0
  approveForm.comment = ''
  approveDialog.value = true
}

const confirmApprove = async () => {
  try {
    await claimRecordApi.approve(approveForm.id, { approved_amount: approveForm.approvedAmount, comment: approveForm.comment })
    ElMessage.success(t('assets.insurance.claim.messages.approveSuccess'))
    approveDialog.value = false
    listRef.value?.refresh()
  } catch (e: any) { ElMessage.error(e?.message) }
}
</script>

