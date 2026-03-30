<template>
  <div class="voucher-template-list-page">
    <BaseListPage
      :key="listVersion"
      :title="t('finance.templates.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchTemplates"
      :selectable="false"
      object-code="VoucherTemplate"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="openCreateDialog"
        >
          {{ t('finance.actions.newTemplate') }}
        </el-button>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="openEditDialog(row)"
        >
          {{ t('common.actions.edit') }}
        </el-button>
        <el-button
          link
          type="success"
          @click="openApplyDialog(row)"
        >
          {{ t('finance.actions.applyTemplate') }}
        </el-button>
        <el-button
          link
          :type="row.isActive ? 'warning' : 'success'"
          @click="toggleTemplateStatus(row)"
        >
          {{ row.isActive ? t('finance.actions.deactivateTemplate') : t('finance.actions.activateTemplate') }}
        </el-button>
        <el-button
          link
          type="danger"
          @click="handleDelete(row)"
        >
          {{ t('common.actions.delete') }}
        </el-button>
      </template>
    </BaseListPage>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="960px"
      destroy-on-close
    >
      <el-form
        ref="templateFormRef"
        :model="templateForm"
        :rules="templateRules"
        label-width="132px"
      >
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item
              :label="t('finance.templates.form.code')"
              prop="code"
            >
              <el-input
                v-model="templateForm.code"
                :placeholder="t('finance.templates.form.codePlaceholder')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              :label="t('finance.templates.form.name')"
              prop="name"
            >
              <el-input
                v-model="templateForm.name"
                :placeholder="t('finance.templates.form.namePlaceholder')"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item
              :label="t('finance.templates.form.businessType')"
              prop="businessType"
            >
              <el-select
                v-model="templateForm.businessType"
                class="full-width"
                :placeholder="t('common.placeholders.select')"
              >
                <el-option
                  v-for="option in businessTypeOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="t('finance.templates.form.active')">
              <el-switch v-model="templateForm.isActive" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item
          :label="t('finance.templates.form.description')"
          prop="description"
        >
          <el-input
            v-model="templateForm.description"
            type="textarea"
            :rows="3"
            :placeholder="t('finance.templates.form.descriptionPlaceholder')"
          />
        </el-form-item>

        <div class="entries-section">
          <div class="entries-section__header">
            <div>
              <h4>{{ t('finance.templates.form.entries') }}</h4>
              <p>{{ t('finance.templates.form.entriesHint') }}</p>
            </div>
            <el-button
              type="primary"
              plain
              :icon="Plus"
              @click="addTemplateEntry"
            >
              {{ t('finance.actions.addEntry') }}
            </el-button>
          </div>

          <el-table
            :data="templateForm.entries"
            border
            size="small"
            class="entries-table"
          >
            <el-table-column
              :label="t('finance.templates.form.entryAccountCode')"
              min-width="150"
            >
              <template #default="{ row }">
                <el-input
                  v-model="row.accountCode"
                  :placeholder="t('finance.templates.form.entryAccountCodePlaceholder')"
                />
              </template>
            </el-table-column>
            <el-table-column
              :label="t('finance.templates.form.entryAccountName')"
              min-width="180"
            >
              <template #default="{ row }">
                <el-input
                  v-model="row.accountName"
                  :placeholder="t('finance.templates.form.entryAccountNamePlaceholder')"
                />
              </template>
            </el-table-column>
            <el-table-column
              :label="t('finance.templates.form.entrySide')"
              width="130"
            >
              <template #default="{ row }">
                <el-select
                  v-model="row.side"
                  class="full-width"
                >
                  <el-option
                    :label="t('finance.templates.form.debit')"
                    value="debit"
                  />
                  <el-option
                    :label="t('finance.templates.form.credit')"
                    value="credit"
                  />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column
              :label="t('finance.templates.form.entryAmount')"
              width="160"
            >
              <template #default="{ row }">
                <el-input-number
                  v-model="row.amount"
                  class="full-width"
                  :min="0"
                  :precision="2"
                  :step="100"
                />
              </template>
            </el-table-column>
            <el-table-column
              :label="t('finance.templates.form.entryDescription')"
              min-width="220"
            >
              <template #default="{ row }">
                <el-input
                  v-model="row.description"
                  :placeholder="t('finance.templates.form.entryDescriptionPlaceholder')"
                />
              </template>
            </el-table-column>
            <el-table-column
              :label="t('common.columns.actions')"
              width="88"
              fixed="right"
            >
              <template #default="{ $index }">
                <el-button
                  link
                  type="danger"
                  :disabled="templateForm.entries.length === 1"
                  @click="removeTemplateEntry($index)"
                >
                  {{ t('common.actions.delete') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">
          {{ t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="submitTemplate"
        >
          {{ t('common.actions.save') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="applyDialogVisible"
      :title="t('finance.templates.apply.title')"
      width="520px"
      destroy-on-close
    >
      <el-form
        ref="applyFormRef"
        :model="applyForm"
        :rules="applyRules"
        label-width="124px"
      >
        <el-form-item :label="t('finance.templates.apply.template')">
          <el-input
            :model-value="selectedTemplate?.name || ''"
            readonly
          />
        </el-form-item>
        <el-form-item
          :label="t('finance.templates.apply.voucherDate')"
          prop="voucherDate"
        >
          <el-date-picker
            v-model="applyForm.voucherDate"
            class="full-width"
            type="date"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item :label="t('finance.templates.apply.summary')">
          <el-input
            v-model="applyForm.summary"
            :placeholder="t('finance.templates.apply.summaryPlaceholder')"
          />
        </el-form-item>
        <el-form-item :label="t('finance.templates.apply.totalAmount')">
          <el-input-number
            v-model="applyForm.totalAmount"
            class="full-width"
            :min="0"
            :precision="2"
            :step="100"
          />
        </el-form-item>
        <el-form-item :label="t('finance.templates.apply.notes')">
          <el-input
            v-model="applyForm.notes"
            type="textarea"
            :rows="3"
            :placeholder="t('finance.templates.apply.notesPlaceholder')"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="applyDialogVisible = false">
          {{ t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="applying"
          @click="submitApply"
        >
          {{ t('finance.actions.applyTemplate') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

import BaseListPage from '@/components/common/BaseListPage.vue'
import { voucherTemplateApi } from '@/api/finance'
import type { SearchField, TableColumn } from '@/types/common'
import type { VoucherTemplate, VoucherTemplateEntry, VoucherTemplateApplyPayload } from '@/types/finance'

type TemplateEntrySide = 'debit' | 'credit'

interface TemplateEntryFormState {
  accountCode: string
  accountName: string
  amount: number
  description: string
  side: TemplateEntrySide
}

interface TemplateFormState {
  businessType: string
  code: string
  description: string
  entries: TemplateEntryFormState[]
  isActive: boolean
  name: string
}

interface TemplateApplyFormState {
  notes: string
  summary: string
  totalAmount: number
  voucherDate: string
}

const router = useRouter()
const { t } = useI18n()

const listVersion = ref(0)
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const applying = ref(false)
const editingTemplateId = ref('')
const selectedTemplate = ref<VoucherTemplate | null>(null)
const applyDialogVisible = ref(false)

const templateFormRef = ref<FormInstance>()
const applyFormRef = ref<FormInstance>()

const createEmptyTemplateEntry = (): TemplateEntryFormState => ({
  accountCode: '',
  accountName: '',
  amount: 0,
  description: '',
  side: 'debit',
})

const createEmptyTemplateForm = (): TemplateFormState => ({
  businessType: '',
  code: '',
  description: '',
  entries: [createEmptyTemplateEntry()],
  isActive: true,
  name: '',
})

const createEmptyApplyForm = (): TemplateApplyFormState => ({
  notes: '',
  summary: '',
  totalAmount: 0,
  voucherDate: new Date().toISOString().slice(0, 10),
})

const templateForm = reactive<TemplateFormState>(createEmptyTemplateForm())
const applyForm = reactive<TemplateApplyFormState>(createEmptyApplyForm())

const businessTypeOptions = computed(() => [
  { label: t('finance.businessType.purchase'), value: 'purchase' },
  { label: t('finance.businessType.depreciation'), value: 'depreciation' },
  { label: t('finance.businessType.disposal'), value: 'disposal' },
  { label: t('finance.businessType.inventory'), value: 'inventory' },
  { label: t('finance.businessType.other'), value: 'other' },
])

const businessTypeLabelMap = computed(() => {
  return businessTypeOptions.value.reduce<Record<string, string>>((accumulator, option) => {
    accumulator[option.value] = option.label
    return accumulator
  }, {})
})

const dialogTitle = computed(() => {
  return dialogMode.value === 'create'
    ? t('finance.templates.dialog.createTitle')
    : t('finance.templates.dialog.editTitle')
})

const searchFields = computed<SearchField[]>(() => [
  {
    prop: 'code',
    label: t('finance.templates.columns.code'),
    type: 'input',
    placeholder: t('common.placeholders.input'),
  },
  {
    prop: 'name',
    label: t('finance.templates.columns.name'),
    type: 'input',
    placeholder: t('common.placeholders.input'),
  },
  {
    prop: 'businessType',
    label: t('finance.templates.columns.businessType'),
    type: 'select',
    options: businessTypeOptions.value,
  },
  {
    prop: 'isActive',
    label: t('finance.templates.columns.isActive'),
    type: 'select',
    options: [
      { label: t('common.status.active'), value: true },
      { label: t('common.status.inactive'), value: false },
    ],
  },
])

const columns = computed<TableColumn[]>(() => [
  {
    prop: 'code',
    label: t('finance.templates.columns.code'),
    width: 160,
    fixed: 'left',
  },
  {
    prop: 'name',
    label: t('finance.templates.columns.name'),
    minWidth: 220,
  },
  {
    prop: 'businessType',
    label: t('finance.templates.columns.businessType'),
    width: 160,
    format: (value: string) => resolveBusinessTypeLabel(value),
  },
  {
    prop: 'isActive',
    label: t('finance.templates.columns.isActive'),
    width: 120,
    tagType: (row: VoucherTemplate) => (row.isActive ? 'success' : 'info'),
    format: (_value: boolean, row: VoucherTemplate) => {
      return row.isActive ? t('common.status.active') : t('common.status.inactive')
    },
  },
  {
    prop: 'updatedAt',
    label: t('common.columns.updatedAt'),
    width: 180,
  },
  {
    prop: 'actions',
    label: t('common.columns.actions'),
    width: 260,
    fixed: 'right',
  },
])

const templateRules = computed<FormRules<TemplateFormState>>(() => ({
  code: [
    { required: true, message: t('finance.templates.validation.codeRequired'), trigger: 'blur' },
  ],
  name: [
    { required: true, message: t('finance.templates.validation.nameRequired'), trigger: 'blur' },
  ],
  businessType: [
    { required: true, message: t('finance.templates.validation.businessTypeRequired'), trigger: 'change' },
  ],
}))

const applyRules = computed<FormRules<TemplateApplyFormState>>(() => ({
  voucherDate: [
    { required: true, message: t('finance.templates.validation.voucherDateRequired'), trigger: 'change' },
  ],
}))

const fetchTemplates = async (params: Record<string, unknown>) => {
  return voucherTemplateApi.listTemplates(params)
}

const resolveBusinessTypeLabel = (businessType: string) => {
  return businessTypeLabelMap.value[businessType] || businessType
}

const normalizeTemplateEntries = (template: VoucherTemplate): TemplateEntryFormState[] => {
  const rawConfig = template.templateConfig || {}
  const rawEntries = Array.isArray((rawConfig as Record<string, unknown>).entries)
    ? ((rawConfig as Record<string, unknown>).entries as VoucherTemplateEntry[])
    : Array.isArray((rawConfig as Record<string, unknown>).lines)
      ? ((rawConfig as Record<string, unknown>).lines as VoucherTemplateEntry[])
      : []

  if (!rawEntries.length) {
    return [createEmptyTemplateEntry()]
  }

  return rawEntries.map((entry) => {
    const debitAmount = Number((entry as any).debitAmount ?? (entry as any).debit_amount ?? 0)
    const creditAmount = Number((entry as any).creditAmount ?? (entry as any).credit_amount ?? 0)
    const fallbackAmount = Number((entry as any).amount ?? 0)
    const side = String((entry as any).side || (entry as any).debitOrCredit || (debitAmount > 0 ? 'debit' : 'credit'))

    return {
      accountCode: String((entry as any).accountCode ?? (entry as any).account_code ?? ''),
      accountName: String((entry as any).accountName ?? (entry as any).account_name ?? ''),
      amount: debitAmount > 0 ? debitAmount : creditAmount > 0 ? creditAmount : fallbackAmount,
      description: String((entry as any).description ?? ''),
      side: side === 'credit' ? 'credit' : 'debit',
    }
  })
}

const resetTemplateForm = () => {
  Object.assign(templateForm, createEmptyTemplateForm())
}

const resetApplyForm = () => {
  Object.assign(applyForm, createEmptyApplyForm())
}

const refreshList = () => {
  listVersion.value += 1
}

const addTemplateEntry = () => {
  templateForm.entries.push(createEmptyTemplateEntry())
}

const removeTemplateEntry = (index: number) => {
  if (templateForm.entries.length === 1) return
  templateForm.entries.splice(index, 1)
}

const openCreateDialog = () => {
  dialogMode.value = 'create'
  editingTemplateId.value = ''
  resetTemplateForm()
  dialogVisible.value = true
}

const openEditDialog = async (row: VoucherTemplate) => {
  dialogMode.value = 'edit'
  editingTemplateId.value = row.id

  try {
    const detail = await voucherTemplateApi.getTemplate(row.id)
    Object.assign(templateForm, {
      businessType: String(detail.businessType || ''),
      code: detail.code || '',
      description: detail.description || '',
      entries: normalizeTemplateEntries(detail),
      isActive: Boolean(detail.isActive),
      name: detail.name || '',
    })
    dialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(error?.message || t('common.messages.loadFailed'))
  }
}

const buildTemplatePayload = () => {
  return {
    businessType: templateForm.businessType,
    code: templateForm.code.trim(),
    description: templateForm.description.trim(),
    isActive: templateForm.isActive,
    name: templateForm.name.trim(),
    templateConfig: {
      businessType: templateForm.businessType,
      entries: templateForm.entries.map((entry) => ({
        accountCode: entry.accountCode.trim(),
        accountName: entry.accountName.trim(),
        creditAmount: entry.side === 'credit' ? Number(entry.amount || 0) : 0,
        debitAmount: entry.side === 'debit' ? Number(entry.amount || 0) : 0,
        description: entry.description.trim(),
      })),
    },
  }
}

const validateTemplateEntries = () => {
  if (!templateForm.entries.length) {
    ElMessage.warning(t('finance.templates.validation.entriesRequired'))
    return false
  }

  const invalidEntry = templateForm.entries.find((entry) => {
    return !entry.accountCode.trim() || !entry.accountName.trim() || Number(entry.amount) <= 0
  })

  if (invalidEntry) {
    ElMessage.warning(t('finance.templates.validation.entryIncomplete'))
    return false
  }

  return true
}

const submitTemplate = async () => {
  const valid = await templateFormRef.value?.validate().catch(() => false)
  if (!valid || !validateTemplateEntries()) return

  submitting.value = true

  try {
    const payload = buildTemplatePayload()
    if (dialogMode.value === 'create') {
      await voucherTemplateApi.createTemplate(payload)
      ElMessage.success(t('finance.templates.messages.createSuccess'))
    } else {
      await voucherTemplateApi.updateTemplate(editingTemplateId.value, payload)
      ElMessage.success(t('finance.templates.messages.updateSuccess'))
    }

    dialogVisible.value = false
    refreshList()
  } catch (error: any) {
    ElMessage.error(error?.message || t('common.messages.operationFailed'))
  } finally {
    submitting.value = false
  }
}

const toggleTemplateStatus = async (row: VoucherTemplate) => {
  const isDeactivating = row.isActive
  const confirmMessage = isDeactivating
    ? t('finance.templates.messages.deactivateConfirm', { name: row.name })
    : t('finance.templates.messages.activateConfirm', { name: row.name })

  try {
    await ElMessageBox.confirm(confirmMessage, t('common.actions.confirm'), {
      type: isDeactivating ? 'warning' : 'info',
    })
  } catch {
    return
  }

  try {
    if (isDeactivating) {
      await voucherTemplateApi.deactivateTemplate(row.id)
    } else {
      await voucherTemplateApi.activateTemplate(row.id)
    }

    ElMessage.success(
      isDeactivating
        ? t('finance.templates.messages.deactivateSuccess')
        : t('finance.templates.messages.activateSuccess')
    )
    refreshList()
  } catch (error: any) {
    ElMessage.error(error?.message || t('common.messages.operationFailed'))
  }
}

const handleDelete = async (row: VoucherTemplate) => {
  try {
    await ElMessageBox.confirm(
      t('finance.templates.messages.deleteConfirm', { name: row.name }),
      t('common.actions.delete'),
      { type: 'warning' }
    )
  } catch {
    return
  }

  try {
    await voucherTemplateApi.deleteTemplate(row.id)
    ElMessage.success(t('finance.templates.messages.deleteSuccess'))
    refreshList()
  } catch (error: any) {
    ElMessage.error(error?.message || t('common.messages.operationFailed'))
  }
}

const openApplyDialog = (row: VoucherTemplate) => {
  selectedTemplate.value = row
  resetApplyForm()
  applyForm.summary = `${t('finance.templates.apply.summaryPrefix')} ${row.name}`
  applyDialogVisible.value = true
}

const submitApply = async () => {
  const valid = await applyFormRef.value?.validate().catch(() => false)
  if (!valid || !selectedTemplate.value) return

  applying.value = true

  try {
    const payload: VoucherTemplateApplyPayload = {
      notes: applyForm.notes.trim() || undefined,
      summary: applyForm.summary.trim() || undefined,
      totalAmount: Number(applyForm.totalAmount || 0),
      voucherDate: applyForm.voucherDate,
    }

    const voucher = await voucherTemplateApi.applyTemplate(selectedTemplate.value.id, payload)
    ElMessage.success(t('finance.templates.messages.applySuccess'))
    applyDialogVisible.value = false
    if (voucher?.id) {
      await router.push(`/finance/vouchers/${voucher.id}`)
    } else {
      refreshList()
    }
  } catch (error: any) {
    ElMessage.error(error?.message || t('common.messages.operationFailed'))
  } finally {
    applying.value = false
  }
}
</script>

<style scoped>
.voucher-template-list-page {
  padding: 0;
}

.entries-section {
  margin-top: 12px;
}

.entries-section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.entries-section__header h4 {
  margin: 0 0 4px;
  font-size: 15px;
}

.entries-section__header p {
  margin: 0;
  color: #909399;
  font-size: 12px;
}

.entries-table {
  width: 100%;
}

.full-width {
  width: 100%;
}
</style>
