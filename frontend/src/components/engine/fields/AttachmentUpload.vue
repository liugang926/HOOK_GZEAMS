<template>
  <el-upload
    v-model:file-list="fileList"
    action="#"
    :auto-upload="false"
    :on-change="handleChange"
    :on-remove="handleRemove"
    :disabled="disabled"
    multiple
    list-type="text"
  >
    <el-button
      type="primary"
      :disabled="disabled"
    >
      点击上传
    </el-button>
    <template #tip>
      <div class="el-upload__tip">
        支持多文件上传
      </div>
    </template>
  </el-upload>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: any[]
  field: any
  disabled?: boolean
}>()

const emit = defineEmits(['update:modelValue'])

const fileList = ref<any[]>([])

// Init file list from model value
watch(() => props.modelValue, (val) => {
    if (val && Array.isArray(val) && fileList.value.length === 0) {
        fileList.value = val.map((item: any, index: number) => ({
            name: item.name || `File ${index + 1}`,
            url: item.url
        }))
    }
}, { immediate: true })

const handleChange = (file: any, files: any[]) => {
    // In real app, we might upload immediately or just keep file objects
    // For now, update model with mock data structure
    fileList.value = files
    updateModel()
}

const handleRemove = (file: any, files: any[]) => {
    fileList.value = files
    updateModel()
}

const updateModel = () => {
    // Map Element Plus file objects to our data structure
    const val = fileList.value.map(f => ({
        name: f.name,
        // url: f.url // If uploaded
    }))
    emit('update:modelValue', val)
}
</script>
