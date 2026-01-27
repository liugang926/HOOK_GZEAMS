<template>
  <div class="base-file-upload">
    <!-- Upload trigger -->
    <el-upload
      ref="uploadRef"
      :action="uploadUrl"
      :headers="uploadHeaders"
      :data="uploadData"
      :name="name"
      :with-credentials="withCredentials"
      :multiple="multiple"
      :accept="accept"
      :limit="limit"
      :disabled="disabled"
      :http-request="customRequest ? customRequestFn : undefined"
      :before-upload="beforeUpload"
      :on-preview="handlePreview"
      :on-remove="handleRemove"
      :on-success="handleSuccess"
      :on-error="handleError"
      :on-progress="handleProgress"
      :on-change="handleChange"
      :on-exceed="handleExceed"
      :file-list="internalFileList"
      :drag="drag"
      :list-type="listType"
      :auto-upload="autoUpload"
      :show-file-list="showFileList"
    >
      <!-- Drag drop area -->
      <template v-if="drag">
        <div class="upload-drag-area">
          <el-icon class="upload-icon">
            <UploadFilled />
          </el-icon>
          <div class="upload-text">
            <p>Drag files to here or <em>click to upload</em></p>
            <p
              v-if="tip"
              class="upload-tip"
            >
              {{ tip }}
            </p>
          </div>
        </div>
      </template>

      <!-- Button trigger (default) -->
      <template v-else>
        <el-button
          :type="buttonType"
          :icon="Upload"
          :disabled="disabled"
        >
          {{ buttonText }}
        </el-button>
      </template>

      <!-- Upload tip (non-drag mode) -->
      <template
        v-if="tip && !drag"
        #tip
      >
        <div class="upload-tip-inline">
          {{ tip }}
        </div>
      </template>
    </el-upload>

    <!-- File list preview dialog -->
    <el-dialog
      v-model="previewVisible"
      title="File Preview"
      width="800px"
      append-to-body
    >
      <div class="preview-container">
        <img
          v-if="isImage(previewFile)"
          :src="previewFile.url"
          :alt="previewFile.name"
        >
        <div
          v-else
          class="preview-file-info"
        >
          <el-icon :size="64">
            <Document />
          </el-icon>
          <p>{{ previewFile.name }}</p>
          <p class="file-meta">
            {{ formatFileSize(previewFile.size) }}
          </p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, UploadFilled, Document } from '@element-plus/icons-vue'
import type { UploadInstance, UploadRequestOptions, UploadUserFile, UploadRawFile } from 'element-plus'
import type { AxiosProgressEvent } from 'axios'

/**
 * Upload file type
 */
export interface UploadFile {
  id?: string
  name: string
  url?: string
  size?: number
  type?: string
  status?: 'ready' | 'uploading' | 'success' | 'fail'
  percentage?: number
  response?: any
}

interface Props {
  modelValue?: UploadFile[]
  action?: string
  headers?: Record<string, string>
  data?: Record<string, any>
  name?: string
  withCredentials?: boolean
  multiple?: boolean
  accept?: string
  limit?: number
  disabled?: boolean
  drag?: boolean
  listType?: 'text' | 'picture' | 'picture-card'
  autoUpload?: boolean
  showFileList?: boolean
  buttonText?: string
  buttonType?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text' | 'default'
  tip?: string
  maxSize?: number // in bytes
  maxFiles?: number
  allowedTypes?: string[]
  customRequest?: (options: UploadRequestOptions) => Promise<any>
}

interface Emits {
  (e: 'update:modelValue', files: UploadFile[]): void
  (e: 'change', file: UploadFile, files: UploadFile[]): void
  (e: 'upload', file: UploadFile): void
  (e: 'remove', file: UploadFile): void
  (e: 'preview', file: UploadFile): void
  (e: 'success', response: any, file: UploadFile): void
  (e: 'error', error: Error, file: UploadFile): void
  (e: 'progress', event: AxiosProgressEvent, file: UploadFile): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  action: '/api/system/files/upload/',
  name: 'file',
  withCredentials: true,
  multiple: false,
  limit: 1,
  disabled: false,
  drag: false,
  listType: 'picture-card',
  autoUpload: true,
  showFileList: true,
  buttonText: 'Upload File',
  buttonType: 'primary',
  maxSize: 100 * 1024 * 1024, // 100MB
  maxFiles: 1
})

const emit = defineEmits<Emits>()

const uploadRef = ref<UploadInstance>()
const internalFileList = ref<UploadUserFile[]>([])
const previewVisible = ref(false)
const previewFile = ref<UploadFile>({} as UploadFile)

// Upload URL (can be overridden by action prop)
const uploadUrl = computed(() => props.action)

// Upload headers with auth token
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('access_token')
  const headers = { ...props.headers }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
})

// Upload additional data
const uploadData = computed(() => props.data)

// Sync internal file list with modelValue
watch(
  () => props.modelValue,
  (newFiles) => {
    internalFileList.value = newFiles.map(file => ({
      name: file.name,
      url: file.url,
      size: file.size,
      status: file.status || 'success',
      uid: file.id || Date.now() + Math.random(),
      response: file.response
    }))
  },
  { immediate: true, deep: true }
)

// Format file size
const formatFileSize = (bytes?: number): string => {
  if (!bytes) return '-'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Check if file is an image
const isImage = (file: UploadFile): boolean => {
  if (!file || !file.type) return false
  return file.type.startsWith('image/')
}

// Validate file before upload
const beforeUpload = (rawFile: UploadRawFile) => {
  // Check file size
  if (props.maxSize && rawFile.size > props.maxSize) {
    ElMessage.error(`File size cannot exceed ${formatFileSize(props.maxSize)}`)
    return false
  }

  // Check file type
  if (props.allowedTypes && props.allowedTypes.length > 0) {
    const fileExt = rawFile.name.split('.').pop()?.toLowerCase()
    const isValidType = props.allowedTypes.some(type => {
      if (type.startsWith('.')) {
        return fileExt === type.substring(1)
      }
      return rawFile.type.includes(type)
    })
    if (!isValidType) {
      ElMessage.error(`File type not allowed. Allowed types: ${props.allowedTypes.join(', ')}`)
      return false
    }
  }

  return true
}

// Custom request handler
const customRequestFn = async (options: UploadRequestOptions) => {
  const { file, onProgress, onSuccess, onError } = options
  try {
    if (props.customRequest) {
      const response = await props.customRequest(options)
      onSuccess(response)
    } else {
      // Default to el-upload's built-in handling
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            onProgress({ percent: (e.loaded / e.total) * 100 } as AxiosProgressEvent)
          }
        })
        xhr.addEventListener('load', () => {
          if (xhr.status < 200 || xhr.status >= 300) {
            onError(new Error(xhr.statusText))
            return reject(new Error(xhr.statusText))
          }
          const response = JSON.parse(xhr.responseText)
          onSuccess(response)
          resolve(response)
        })
        xhr.addEventListener('error', () => {
          onError(new Error('Upload failed'))
          reject(new Error('Upload failed'))
        })

        const formData = new FormData()
        formData.append(props.name, file)
        Object.entries(uploadData.value).forEach(([key, value]) => {
          formData.append(key, value as string)
        })

        xhr.open('POST', uploadUrl.value, true)
        Object.entries(uploadHeaders.value).forEach(([key, value]) => {
          xhr.setRequestHeader(key, value)
        })
        xhr.send(formData)
      })
    }
  } catch (error) {
    onError(error as Error)
  }
}

// Handle file preview
const handlePreview = (file: UploadUserFile) => {
  const uploadFile: UploadFile = {
    id: file.uid.toString(),
    name: file.name,
    url: file.url,
    size: file.size,
    type: file.raw?.type
  }
  emit('preview', uploadFile)
  previewFile.value = uploadFile
  previewVisible.value = true
}

// Handle file remove
const handleRemove = async (file: UploadUserFile) => {
  const uploadFile: UploadFile = {
    id: file.uid.toString(),
    name: file.name,
    url: file.url,
    size: file.size,
    status: file.status as any
  }

  // Confirm removal
  try {
    await ElMessageBox.confirm('Are you sure to remove this file?', 'Confirm', {
      type: 'warning'
    })
    emit('remove', uploadFile)
    return true
  } catch {
    return false
  }
}

// Handle upload success
const handleSuccess = (response: any, file: UploadUserFile) => {
  const uploadFile: UploadFile = {
    id: response.id || file.uid.toString(),
    name: file.name,
    url: response.url || response.file?.url || URL.createObjectURL(file.raw!),
    size: file.size,
    type: file.raw?.type,
    status: 'success',
    response
  }

  // Update internal file list
  const index = internalFileList.value.findIndex(f => f.uid === file.uid)
  if (index >= 0) {
    internalFileList.value[index] = { ...file, url: uploadFile.url, response }
  }

  // Emit events
  emit('success', response, uploadFile)
  emit('change', uploadFile, internalFileList.value.map(f => ({
    id: f.uid.toString(),
    name: f.name,
    url: f.url,
    size: f.size,
    status: f.status as any,
    response: f.response
  })))

  ElMessage.success('File uploaded successfully')
}

// Handle upload error
const handleError = (error: Error, file: UploadUserFile) => {
  const uploadFile: UploadFile = {
    id: file.uid.toString(),
    name: file.name,
    size: file.size,
    status: 'fail'
  }

  emit('error', error, uploadFile)

  const message = error?.message || 'Upload failed'
  ElMessage.error(message)
}

// Handle upload progress
const handleProgress = (event: AxiosProgressEvent, file: UploadUserFile) => {
  const uploadFile: UploadFile = {
    id: file.uid.toString(),
    name: file.name,
    size: file.size,
    status: 'uploading',
    percentage: event.percent
  }

  emit('progress', event, uploadFile)
}

// Handle file list change
const handleChange = (file: UploadUserFile, files: UploadUserFile[]) => {
  const uploadFile: UploadFile = {
    id: file.uid.toString(),
    name: file.name,
    size: file.size,
    status: file.status as any
  }

  emit('change', uploadFile, files.map(f => ({
    id: f.uid.toString(),
    name: f.name,
    url: f.url,
    size: f.size,
    status: f.status as any,
    response: f.response
  })))
}

// Handle exceed limit
const handleExceed = () => {
  ElMessage.warning(`Maximum ${props.limit} files allowed`)
}

// Public methods
const submit = () => {
  uploadRef.value?.submit()
}

const clearFiles = () => {
  uploadRef.value?.clearFiles()
  internalFileList.value = []
  emit('update:modelValue', [])
}

const abort = (file?: UploadUserFile) => {
  if (file) {
    uploadRef.value?.abort(file)
  } else {
    uploadRef.value?.abort()
  }
}

defineExpose({
  uploadRef,
  submit,
  clearFiles,
  abort
})
</script>

<style scoped>
.base-file-upload {
  display: inline-block;
  width: 100%;
}

.upload-drag-area {
  padding: 40px;
  text-align: center;
  border: 2px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-drag-area:hover {
  border-color: var(--el-color-primary);
}

.upload-icon {
  font-size: 48px;
  color: var(--el-text-color-placeholder);
  margin-bottom: 16px;
}

.upload-text p {
  margin: 0;
  color: var(--el-text-color-regular);
}

.upload-text em {
  color: var(--el-color-primary);
  font-style: normal;
}

.upload-tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.upload-tip-inline {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.preview-container {
  text-align: center;
}

.preview-container img {
  max-width: 100%;
  max-height: 500px;
  border-radius: 4px;
}

.preview-file-info {
  padding: 20px;
}

.preview-file-info .el-icon {
  color: var(--el-text-color-placeholder);
  margin-bottom: 16px;
}

.preview-file-info p {
  margin: 8px 0;
}

.file-meta {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

:deep(.el-upload-list__item) {
  transition: all 0.3s;
}

:deep(.el-upload-list__item:hover) {
  background-color: var(--el-fill-color-light);
}
</style>
