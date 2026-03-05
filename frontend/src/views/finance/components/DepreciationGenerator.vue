<template>
  <el-dialog
    :title="lt('depreciationDialog.title')"
    :model-value="modelValue"
    width="500px"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item
        :label="lt('depreciationDialog.period')"
        prop="period"
      >
        <el-date-picker
          v-model="form.period"
          type="month"
          value-format="YYYY-MM"
          :placeholder="lt('depreciationDialog.periodPlaceholder')"
          style="width: 100%"
        />
      </el-form-item>

      <div
        v-if="calculating"
        class="progress-area"
      >
        <div class="mb-2">
          {{ lt('depreciationDialog.calculating') }}
        </div>
        <el-progress
          :percentage="progress"
          :status="progressStatus"
        />
      </div>
    </el-form>

    <template #footer>
      <el-button @click="close">
        {{ t('common.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="calculating"
        @click="handleCalculate"
      >
        {{ lt('depreciationDialog.start') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { depreciationApi } from '@/api/depreciation'

defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits(['update:modelValue', 'success'])
const { t } = useI18n()
const lt = (key: string) => {
  const plainKey = `finance.${key}`
  const plainText = t(plainKey)
  if (plainText !== plainKey) return plainText
  const nestedKey = `finance.finance.${key}`
  const nestedText = t(nestedKey)
  return nestedText !== nestedKey ? nestedText : plainText
}

const formRef = ref()
const calculating = ref(false)
const progress = ref(0)
const progressStatus = ref<'success' | 'exception' | ''>('')
let pollTimer: ReturnType<typeof setInterval> | null = null

const form = reactive({
  period: ''
})

const rules = {
  period: [{ required: true, message: lt('depreciationDialog.validation.periodRequired'), trigger: 'change' }]
}

const close = () => {
  emit('update:modelValue', false)
  progress.value = 0
  calculating.value = false
  if (pollTimer) clearInterval(pollTimer)
}

const handleCalculate = async () => {
  if (!formRef.value) return
  await formRef.value.validate()

  calculating.value = true
  progress.value = 0
  progressStatus.value = ''

  try {
    const { taskId } = await depreciationApi.calculate({ period: form.period })
    startPolling(taskId)
  } catch (e: any) {
    ElMessage.error(e.message || lt('depreciationDialog.messages.startFailed'))
    calculating.value = false
  }
}

const startPolling = (taskId: string) => {
  pollTimer = setInterval(async () => {
    try {
      const res = await depreciationApi.getCalculationStatus(taskId)
      progress.value = Math.floor((res.processed / res.total) * 100) || 0

      if (res.status === 'completed') {
        if (pollTimer) clearInterval(pollTimer)
        progress.value = 100
        progressStatus.value = 'success'
        ElMessage.success(lt('depreciationDialog.messages.completed'))
        setTimeout(() => {
          emit('success')
          close()
        }, 1000)
      } else if (res.status === 'failed') {
        if (pollTimer) clearInterval(pollTimer)
        progressStatus.value = 'exception'
        ElMessage.error(res.error || lt('depreciationDialog.messages.failed'))
        calculating.value = false
      }
    } catch (e) {
      console.error(e)
    }
  }, 2000)
}

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.progress-area {
  margin-top: 20px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}
</style>
