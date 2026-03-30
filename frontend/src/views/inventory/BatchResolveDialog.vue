<template>
  <el-dialog
    :model-value="modelValue"
    :title="t('inventory.batchResolveDialog.title')"
    width="640px"
    destroy-on-close
    @close="handleClose"
  >
    <el-alert
      class="batch-resolve-dialog__summary"
      type="info"
      :closable="false"
      show-icon
      :title="t('inventory.batchResolveDialog.summary', { count: differences.length })"
    />

    <div class="batch-resolve-dialog__preview">
      <div class="batch-resolve-dialog__preview-header">
        {{ t('inventory.batchResolveDialog.previewTitle') }}
      </div>

      <el-table
        :data="previewDifferences"
        size="small"
        max-height="240"
        border
      >
        <el-table-column
          prop="assetCode"
          :label="t('inventory.batchResolveDialog.columns.assetCode')"
          min-width="140"
        >
          <template #default="{ row }">
            {{ getAssetCode(row) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="assetName"
          :label="t('inventory.batchResolveDialog.columns.assetName')"
          min-width="180"
        >
          <template #default="{ row }">
            {{ getAssetName(row) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="differenceType"
          :label="t('inventory.batchResolveDialog.columns.differenceType')"
          width="140"
        >
          <template #default="{ row }">
            <el-tag :type="getDifferenceTagType(row.differenceType)">
              {{ getDifferenceLabel(row.differenceType, row.differenceTypeLabel) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="status"
          :label="t('inventory.batchResolveDialog.columns.status')"
          width="120"
        >
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status, row.statusLabel) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div
        v-if="overflowCount > 0"
        class="batch-resolve-dialog__overflow"
      >
        {{ t('inventory.batchResolveDialog.overflow', { count: overflowCount }) }}
      </div>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="110px"
      class="batch-resolve-dialog__form"
    >
      <el-form-item
        :label="t('inventory.batchResolveDialog.fields.action')"
        prop="action"
      >
        <el-select
          v-model="form.action"
          style="width: 100%"
          :placeholder="t('inventory.batchResolveDialog.placeholders.action')"
        >
          <el-option
            :label="t('inventory.batchResolveDialog.actions.confirm')"
            value="confirm"
          />
          <el-option
            :label="t('inventory.batchResolveDialog.actions.adjust')"
            value="adjust"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="t('inventory.batchResolveDialog.fields.remark')"
        prop="remark"
      >
        <el-input
          v-model="form.remark"
          type="textarea"
          :rows="4"
          :placeholder="t('inventory.batchResolveDialog.placeholders.remark')"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        {{ t('common.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ t('common.actions.confirm') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { inventoryApi } from '@/api/inventory'
import type {
  DifferenceResolution,
  InventoryDifference,
  InventoryDifferenceStatus,
  InventoryDifferenceType,
} from '@/types/inventory'
import type { BatchResponse } from '@/types/api'

interface Props {
  modelValue: boolean
  differences: InventoryDifference[]
}

interface FormModel {
  action: DifferenceResolution['action']
  remark: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  resolved: [response: BatchResponse]
}>()

const { t } = useI18n()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive<FormModel>({
  action: 'confirm',
  remark: '',
})

const previewDifferences = computed(() => props.differences.slice(0, 5))
const overflowCount = computed(() => Math.max(props.differences.length - previewDifferences.value.length, 0))

const rules: FormRules<FormModel> = {
  action: [
    {
      required: true,
      message: t('inventory.batchResolveDialog.validation.actionRequired'),
      trigger: 'change',
    },
  ],
  remark: [
    {
      validator: (_rule, value, callback) => {
        if (form.action === 'adjust' && !String(value || '').trim()) {
          callback(new Error(t('inventory.batchResolveDialog.validation.remarkRequired')))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      form.action = 'confirm'
      form.remark = ''
      formRef.value?.clearValidate()
    }
  }
)

const getAssetCode = (difference: InventoryDifference) => {
  if (difference.assetCode) return difference.assetCode
  if (difference.asset && typeof difference.asset === 'object' && 'assetCode' in difference.asset) {
    return String(difference.asset.assetCode || '--')
  }
  if (difference.asset && typeof difference.asset === 'object' && 'code' in difference.asset) {
    return String(difference.asset.code || '--')
  }
  return '--'
}

const getAssetName = (difference: InventoryDifference) => {
  if (difference.assetName) return difference.assetName
  if (difference.asset && typeof difference.asset === 'object' && 'assetName' in difference.asset) {
    return String(difference.asset.assetName || '--')
  }
  if (difference.asset && typeof difference.asset === 'object' && 'name' in difference.asset) {
    return String(difference.asset.name || '--')
  }
  return '--'
}

const getDifferenceTagType = (type: InventoryDifferenceType | string) => {
  const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    normal: 'success',
    missing: 'danger',
    extra: 'warning',
    surplus: 'warning',
    damaged: 'danger',
    location_mismatch: 'info',
    custodian_mismatch: 'info',
  }
  return typeMap[type] || 'info'
}

const getDifferenceLabel = (type: InventoryDifferenceType | string, fallback?: string) => {
  if (fallback) return fallback

  const keyMap: Record<string, string> = {
    normal: 'inventory.differenceList.types.normal',
    missing: 'inventory.differenceList.types.missing',
    extra: 'inventory.differenceList.types.extra',
    surplus: 'inventory.differenceList.types.extra',
    damaged: 'inventory.differenceList.types.damaged',
    location_mismatch: 'inventory.differenceList.types.locationMismatch',
    custodian_mismatch: 'inventory.differenceList.types.custodianMismatch',
  }

  return keyMap[type] ? t(keyMap[type]) : type
}

const getStatusTagType = (status: InventoryDifferenceStatus | string) => {
  const typeMap: Record<string, 'warning' | 'info' | 'primary' | 'success' | 'danger'> = {
    pending: 'warning',
    confirmed: 'info',
    in_review: 'primary',
    approved: 'primary',
    executing: 'primary',
    resolved: 'success',
    ignored: 'danger',
    closed: 'success',
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: InventoryDifferenceStatus | string, fallback?: string) => {
  if (fallback) return fallback

  const keyMap: Record<string, string> = {
    pending: 'inventory.differenceList.statuses.pending',
    confirmed: 'inventory.differenceList.statuses.confirmed',
    in_review: 'inventory.differenceList.statuses.inReview',
    approved: 'inventory.differenceList.statuses.approved',
    executing: 'inventory.differenceList.statuses.executing',
    resolved: 'inventory.differenceList.statuses.resolved',
    ignored: 'inventory.differenceList.statuses.ignored',
    closed: 'inventory.differenceList.statuses.closed',
  }

  return keyMap[status] ? t(keyMap[status]) : status
}

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleSubmit = async () => {
  if (!props.differences.length) {
    ElMessage.warning(t('inventory.batchResolveDialog.messages.noSelection'))
    return
  }

  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const response = await inventoryApi.resolveDifferences({
      differenceIds: props.differences.map((item) => item.id),
      action: form.action,
      remark: form.remark.trim() || undefined,
    })

    const { total, succeeded, failed } = response.summary

    if (failed > 0) {
      ElMessage.warning(
        t('inventory.batchResolveDialog.messages.partialSuccess', {
          succeeded,
          failed,
          total,
        })
      )
    } else {
      ElMessage.success(
        t('inventory.batchResolveDialog.messages.success', {
          count: succeeded,
        })
      )
    }

    emit('resolved', response)
    handleClose()
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.batch-resolve-dialog__summary {
  margin-bottom: 16px;
}

.batch-resolve-dialog__preview {
  margin-bottom: 20px;
}

.batch-resolve-dialog__preview-header {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.batch-resolve-dialog__overflow {
  margin-top: 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.batch-resolve-dialog__form {
  padding-top: 4px;
}
</style>
