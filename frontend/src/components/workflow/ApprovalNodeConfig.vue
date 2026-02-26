<template>
  <div class="approval-config">
    <el-form
      :model="localValue"
      :label-width="locale === 'zh-CN' ? '90px' : '140px'"
      size="small"
    >
      <el-form-item :label="t('workflow.fields.approvalType')">
        <el-radio-group v-model="localValue.approveType">
          <el-radio value="or">
            {{ t('workflow.approvalType.or') }}
          </el-radio>
          <el-radio value="and">
            {{ t('workflow.approvalType.and') }}
          </el-radio>
          <el-radio value="seq">
            {{ t('workflow.approvalType.sequence') }}
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item :label="t('workflow.fields.approver')">
        <ApproverSelector v-model="localValue.approvers" />
      </el-form-item>

      <el-form-item :label="t('workflow.fields.timeout')">
        <el-input-number
          v-model="localValue.timeout"
          :min="1"
          :max="720"
          controls-position="right"
        />
        <span class="unit">{{ t('common.units.hours') }}</span>
      </el-form-item>

      <el-form-item :label="t('workflow.fields.timeoutAction')">
        <el-select v-model="localValue.timeoutAction">
          <el-option
            :label="t('workflow.timeoutAction.pass')"
            value="approve"
          />
          <el-option
            :label="t('workflow.timeoutAction.reject')"
            value="reject"
          />
          <el-option
            :label="t('workflow.timeoutAction.transfer')"
            value="transfer"
          />
        </el-select>
      </el-form-item>

      <el-form-item :label="t('workflow.designer.autoApprove')">
        <el-switch v-model="localValue.autoApprove" />
        <span class="tip">{{ t('workflow.designer.autoApproveHint') }}</span>
      </el-form-item>

      <el-form-item :label="t('workflow.designer.allowTransfer')">
        <el-switch v-model="localValue.allowTransfer" />
      </el-form-item>

      <el-form-item :label="t('workflow.designer.allowAddApprover')">
        <el-switch v-model="localValue.allowAddApprover" />
      </el-form-item>

      <el-form-item :label="t('workflow.designer.rejectMethod')">
        <el-radio-group v-model="localValue.rejectType">
          <el-radio value="to_start">
            {{ t('workflow.designer.rejectToInitiator') }}
          </el-radio>
          <el-radio value="to_prev">
            {{ t('workflow.designer.rejectToPrev') }}
          </el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import ApproverSelector from './ApproverSelector.vue'

const { t } = useI18n()
const locale = computed(() => t('locale'))

interface Props {
  modelValue: Record<string, any>
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, any>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const localValue = computed({
  get: () => props.modelValue || {
    approveType: 'or',
    approvers: [],
    timeout: 72,
    timeoutAction: 'transfer',
    autoApprove: false,
    allowTransfer: true,
    allowAddApprover: false,
    rejectType: 'to_prev'
  },
  set: (val) => emit('update:modelValue', val)
})
</script>

<style scoped>
.approval-config {
  padding: 5px 0;
}

.unit {
  margin-left: 8px;
  color: #909399;
  font-size: 13px;
}

.tip {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}
</style>
