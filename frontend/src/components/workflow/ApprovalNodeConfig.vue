<template>
  <div class="approval-config">
    <el-form
      :model="localValue"
      label-width="90px"
      size="small"
    >
      <el-form-item label="审批方式">
        <el-radio-group v-model="localValue.approveType">
          <el-radio value="or">
            或签（一人通过）
          </el-radio>
          <el-radio value="and">
            会签（全部通过）
          </el-radio>
          <el-radio value="seq">
            依次审批
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="审批人">
        <ApproverSelector v-model="localValue.approvers" />
      </el-form-item>

      <el-form-item label="超时时间">
        <el-input-number
          v-model="localValue.timeout"
          :min="1"
          :max="720"
          controls-position="right"
        />
        <span class="unit">小时</span>
      </el-form-item>

      <el-form-item label="超时操作">
        <el-select v-model="localValue.timeoutAction">
          <el-option
            label="自动通过"
            value="approve"
          />
          <el-option
            label="自动拒绝"
            value="reject"
          />
          <el-option
            label="转交管理员"
            value="transfer"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="自动通过">
        <el-switch v-model="localValue.autoApprove" />
        <span class="tip">审批人与发起人相同时自动通过</span>
      </el-form-item>

      <el-form-item label="允许转交">
        <el-switch v-model="localValue.allowTransfer" />
      </el-form-item>

      <el-form-item label="允许加签">
        <el-switch v-model="localValue.allowAddApprover" />
      </el-form-item>

      <el-form-item label="退回方式">
        <el-radio-group v-model="localValue.rejectType">
          <el-radio value="to_start">
            退回到发起人
          </el-radio>
          <el-radio value="to_prev">
            退回到上一节点
          </el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ApproverSelector from './ApproverSelector.vue'

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
