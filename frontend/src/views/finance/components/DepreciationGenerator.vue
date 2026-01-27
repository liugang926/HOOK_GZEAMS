<template>
  <el-dialog
    title="计提折旧"
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
        label="计提期间"
        prop="period"
      >
        <el-date-picker
          v-model="form.period"
          type="month"
          value-format="YYYY-MM"
          placeholder="选择月份"
          style="width: 100%"
        />
      </el-form-item>
      
      <div
        v-if="calculating"
        class="progress-area"
      >
        <div class="mb-2">
          正在计算中...
        </div>
        <el-progress
          :percentage="progress"
          :status="progressStatus"
        />
      </div>
    </el-form>
    
    <template #footer>
      <el-button @click="close">
        取消
      </el-button>
      <el-button
        type="primary"
        :loading="calculating"
        @click="handleCalculate"
      >
        开始计算
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { depreciationApi } from '@/api/depreciation'

defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const calculating = ref(false)
const progress = ref(0)
const progressStatus = ref<'success' | 'exception' | ''>('')
let pollTimer: any = null

const form = reactive({
  period: '' // YYYY-MM
})

const rules = {
  period: [{ required: true, message: '请选择期间', trigger: 'change' }]
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
    ElMessage.error(e.message || '启动计算失败')
    calculating.value = false
  }
}

const startPolling = (taskId: string) => {
  pollTimer = setInterval(async () => {
    try {
      const res = await depreciationApi.getCalculationStatus(taskId)
      progress.value = Math.floor((res.processed / res.total) * 100) || 0
      
      if (res.status === 'completed') {
        clearInterval(pollTimer)
        progress.value = 100
        progressStatus.value = 'success'
        ElMessage.success('计算完成')
        setTimeout(() => {
          emit('success')
          close()
        }, 1000)
      } else if (res.status === 'failed') {
        clearInterval(pollTimer)
        progressStatus.value = 'exception'
        ElMessage.error(res.error || '计算失败')
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
