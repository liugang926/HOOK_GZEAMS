<template>
  <div class="attachment-upload">
    <!-- Upload trigger -->
    <el-upload
      ref="uploadRef"
      v-model:file-list="uploadFileList"
      :action="uploadUrl"
      :headers="uploadHeaders"
      :auto-upload="autoUpload"
      :disabled="disabled || uploading"
      :on-change="handleChange"
      :on-progress="handleProgress"
      :on-success="handleSuccess"
      :on-error="handleError"
      :on-remove="handleRemove"
      :before-upload="beforeUpload"
      :multiple="allowMultiple"
      :limit="maxCount"
      :on-exceed="handleExceed"
      :list-type="listType"
      :drag="dragUpload"
      class="upload-component"
    >
      <!-- Drag upload area -->
      <div
        v-if="dragUpload"
        class="upload-drag-area"
      >
        <el-icon
          class="upload-icon"
          :size="48"
        >
          <UploadFilled />
        </el-icon>
        <div class="upload-text">
          Drag file here or <em>click to upload</em>
        </div>
        <div
          v-if="hint"
          class="upload-hint"
        >
          {{ hint }}
        </div>
      </div>

      <!-- Button trigger -->
      <el-button
        v-else
        type="primary"
        :disabled="disabled || uploading"
        :loading="uploading"
      >
        <el-icon><Upload /></el-icon>
        {{ uploading ? 'Uploading...' : buttonText }}
      </el-button>

      <!-- File list slot for picture-card type -->
      <template #file="{ file }">
        <div
          v-if="listType === 'picture-card'"
          class="upload-file-card"
        >
          <img
            v-if="isImageUrl(file)"
            :src="file.url"
            class="upload-thumbnail"
            alt="preview"
          >
          <div
            v-else
            class="upload-file-icon"
          >
            <el-icon :size="32">
              <Document />
            </el-icon>
          </div>
          <div
            v-if="file.status === 'uploading'"
            class="upload-progress"
          >
            <el-progress
              type="circle"
              :percentage="parseInt(file.percentage || '0')"
              :width="50"
            />
          </div>
        </div>
      </template>
    </el-upload>

    <!-- Upload progress indicator (for auto-upload: false) -->
    <div
      v-if="!autoUpload && hasPendingFiles && uploading"
      class="upload-status"
    >
      <el-progress
        :percentage="overallProgress"
        :status="uploadStatus"
      >
        <span class="progress-text">{{ uploadStatusText }}</span>
      </el-progress>
    </div>

    <!-- Error message display -->
    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      :closable="true"
      class="upload-error"
      @close="errorMessage = ''"
    />

    <!-- Manual upload button when auto-upload is disabled -->
    <div
      v-if="!autoUpload && hasPendingFiles"
      class="upload-actions"
    >
      <el-button
        type="primary"
        :loading="uploading"
        @click="startUpload"
      >
        Upload {{ pendingFileCount }} File(s)
      </el-button>
      <el-button @click="clearFiles">
        Clear
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadInstance, UploadProps, UploadUserFile, UploadRawFile } from 'element-plus'
import {
  Upload,
  UploadFilled,
  Document
} from '@element-plus/icons-vue'
import { systemFileApi, validateFile, validateFiles } from '@/api/systemFile'

interface FileItem {
  id: string
  fileName: string
  fileSize: number
  url: string
  thumbnailUrl?: string
}

interface UploadOptions {
  objectCode?: string
  instanceId?: string
  fieldCode?: string
}

const props = withDefaults(
  defineProps<{
    modelValue: string[]
    field?: any
    disabled?: boolean
    // Upload options
    autoUpload?: boolean
    allowMultiple?: boolean
    maxCount?: number
    maxSize?: number // in bytes
    allowedTypes?: string[] // MIME types
    dragUpload?: boolean
    listType?: 'text' | 'picture' | 'picture-card'
    buttonText?: string
    hint?: string
    // Object context for upload
    objectCode?: string
    instanceId?: string
    fieldCode?: string
  }>(),
  {
    disabled: false,
    autoUpload: true,
    allowMultiple: true,
    maxCount: 10,
    dragUpload: false,
    listType: 'text',
    buttonText: 'Select File'
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
  'change': [value: string[], files: FileItem[]]
}>()

const uploadRef = ref<UploadInstance>()
const uploadFileList = ref<UploadUserFile[]>([])
const uploading = ref(false)
const uploadProgress = ref(0)
const errorMessage = ref('')
const loadedFileMetadata = ref<Map<string, FileItem>>(new Map())

// Upload URL (using the real endpoint)
const uploadUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL || '/api'}/system/system-files/upload/`
})

// Upload headers with auth token
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  return {
    'Authorization': token ? `Bearer ${token}` : ''
  }
})

// Overall upload progress
const overallProgress = computed(() => uploadProgress.value)

// Upload status
const uploadStatus = computed<'success' | 'exception' | undefined>(() => {
  if (errorMessage.value) return 'exception'
  if (uploadProgress.value === 100) return 'success'
  return undefined
})

// Upload status text
const uploadStatusText = computed(() => {
  if (errorMessage.value) return 'Upload failed'
  if (uploadProgress.value === 100) return 'Upload complete'
  return `Uploading... ${uploadProgress.value}%`
})

// Check if there are pending files
const hasPendingFiles = computed(() => {
  return uploadFileList.value.some(
    f => f.status === 'ready' || f.status === 'uploading'
  )
})

// Count of pending files
const pendingFileCount = computed(() => {
  return uploadFileList.value.filter(
    f => f.status === 'ready'
  ).length
})

// Initialize file list from model value (file IDs)
watch(
  () => props.modelValue,
  async (val) => {
    if (val && Array.isArray(val) && val.length > 0) {
      // Fetch file metadata if we only have IDs
      const ids = val.filter((v: any) => typeof v === 'string' || typeof v === 'object' && v.id)
      if (ids.length > 0) {
        try {
          const metadata = await systemFileApi.getMetadata(ids as string[])
          // Store metadata
          metadata.forEach(file => {
            loadedFileMetadata.value.set(file.id, file)
          })
          // Update file list for display
          syncFileListFromMetadata()
        } catch (error) {
          console.error('Failed to load file metadata:', error)
        }
      }
    }
  },
  { immediate: true }
)

// Sync file list from loaded metadata
function syncFileListFromMetadata() {
  const currentValue = props.modelValue || []
  uploadFileList.value = currentValue
    .filter((v: any) => typeof v === 'string' || v?.id)
    .map((v: any) => {
      const id = typeof v === 'string' ? v : v.id
      const meta = loadedFileMetadata.value.get(id)
      if (meta) {
        return {
          name: meta.fileName,
          url: meta.url,
          status: 'success',
          uid: id,
          response: { data: meta }
        } as UploadUserFile
      }
      return null
    })
    .filter(Boolean) as UploadUserFile[]
}

// Check if file URL is an image
function isImageUrl(file: UploadUserFile): boolean {
  if (!file.url) return false
  const ext = file.url.split('.').pop()?.toLowerCase() || ''
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext)
}

// Before upload validation
const beforeUpload: UploadProps['beforeUpload'] = (rawFile) => {
  const validation = validateFile(rawFile, {
    maxSize: props.maxSize,
    allowedTypes: props.allowedTypes
  })

  if (!validation.valid) {
    errorMessage.value = validation.error || 'File validation failed'
    ElMessage.error(errorMessage.value)
    return false
  }

  errorMessage.value = ''
  return true
}

// Handle file selection
const handleChange: UploadProps['onChange'] = (uploadFile, uploadFiles) => {
  uploadFileList.value = uploadFiles

  // Auto-upload enabled - files will upload automatically
  // Auto-upload disabled - just store the files for manual upload
}

// Handle upload progress
const handleProgress: UploadProps['onProgress'] = (evt) => {
  if (evt.percent) {
    uploadProgress.value = Math.round(evt.percent)
  }
}

// Handle upload success
const handleSuccess: UploadProps['onSuccess'] = (response, file) => {
  if (response.success && response.data) {
    const fileData: FileItem = response.data
    loadedFileMetadata.value.set(fileData.id, fileData)
    updateModelValue()
  } else {
    file.status = 'fail'
    errorMessage.value = response.message || 'Upload failed'
  }
}

// Handle upload error
const handleError: UploadProps['onError'] = (error, file) => {
  file.status = 'fail'
  errorMessage.value = `Upload failed: ${error.message || 'Unknown error'}`
  ElMessage.error(errorMessage.value)
}

// Handle file removal
const handleRemove: UploadProps['onRemove'] = (file) => {
  const index = uploadFileList.value.indexOf(file)
  if (index > -1) {
    uploadFileList.value.splice(index, 1)
    updateModelValue()
  }
}

// Handle exceed max count
const handleExceed: UploadProps['onExceed'] = () => {
  ElMessage.warning(`Maximum ${props.maxCount} file(s) allowed.`)
}

// Start manual upload
function startUpload() {
  if (!uploadRef.value) return

  // Validate all files before upload
  const readyFiles = uploadFileList.value.filter(f => f.status === 'ready')
  const validation = validateFiles(
    readyFiles.map(f => f.raw as File),
    {
      maxCount: props.maxCount,
      maxSize: props.maxSize,
      allowedTypes: props.allowedTypes
    }
  )

  if (!validation.valid) {
    errorMessage.value = validation.error || 'File validation failed'
    ElMessage.error(errorMessage.value)
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  errorMessage.value = ''

  uploadRef.value.submit()
}

// Clear all files
function clearFiles() {
  uploadFileList.value = []
  updateModelValue()
}

// Update model value with current file IDs
function updateModelValue() {
  const fileIds = uploadFileList.value
    .filter(f => f.status === 'success' && f.response?.data?.id)
    .map(f => f.response.data.id)

  const files = fileIds.map(id => loadedFileMetadata.value.get(id)).filter(Boolean) as FileItem[]

  emit('update:modelValue', fileIds)
  emit('change', fileIds, files)
}

// Expose methods
defineExpose({
  startUpload,
  clearFiles
})
</script>

<style scoped lang="scss">
.attachment-upload {
  width: 100%;
}

.upload-component {
  width: 100%;
}

.upload-drag-area {
  padding: 40px;
  text-align: center;
  border: 2px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.3s;

  &:hover {
    border-color: var(--el-color-primary);
  }
}

.upload-icon {
  color: var(--el-text-color-placeholder);
}

.upload-text {
  margin-top: 16px;
  font-size: 14px;
  color: var(--el-text-color-regular);

  em {
    color: var(--el-color-primary);
    font-style: normal;
  }
}

.upload-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.upload-status {
  margin-top: 16px;
}

.progress-text {
  font-size: 12px;
}

.upload-error {
  margin-top: 12px;
}

.upload-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.upload-file-card {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-file-icon {
  font-size: 32px;
  color: var(--el-text-color-placeholder);
}

.upload-progress {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style>
