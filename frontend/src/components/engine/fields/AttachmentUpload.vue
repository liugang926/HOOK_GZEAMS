<template>
  <div class="attachment-upload">
    <!-- Upload trigger -->
    <el-upload
      ref="uploadRef"
      v-model:file-list="uploadFileList"
      action="#"
      :http-request="httpRequest"
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
          {{ $t('common.messages.dragFileHere') }} <em>{{ $t('common.messages.clickToUpload') }}</em>
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
        {{ uploading ? $t('common.messages.uploading') : resolvedButtonText }}
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
              :percentage="Number(file.percentage || 0)"
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
        {{ $t('common.messages.uploadPendingCount', { count: pendingFileCount }) }}
      </el-button>
      <el-button @click="clearFiles">
        {{ $t('common.actions.clear') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { UploadInstance, UploadProps, UploadUserFile, UploadRequestOptions } from 'element-plus'
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

interface UploadSuccessResponse {
  success?: boolean
  data?: FileItem
  message?: string
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
    buttonText: ''
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
  'change': [value: string[], files: FileItem[]]
}>()
const { t } = useI18n()

const uploadRef = ref<UploadInstance>()
const uploadFileList = ref<UploadUserFile[]>([])
const uploading = ref(false)
const uploadProgress = ref(0)
const errorMessage = ref('')
const loadedFileMetadata = ref<Map<string, FileItem>>(new Map())
const activeUploadCount = ref(0)

const resolvedButtonText = computed(() => props.buttonText || t('form.fields.uploadFile'))

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
  if (errorMessage.value) return t('common.messages.operationFailed')
  if (uploadProgress.value === 100) return t('common.messages.uploadComplete')
  return `${t('common.messages.uploading')} ${uploadProgress.value}%`
})

// Check if there are pending files
const hasPendingFiles = computed(() => {
  return uploadFileList.value.some(
    (f: UploadUserFile) => f.status === 'ready' || f.status === 'uploading'
  )
})

// Count of pending files
const pendingFileCount = computed(() => {
  return uploadFileList.value.filter(
    (f: UploadUserFile) => f.status === 'ready'
  ).length
})

// Initialize file list from model value (file IDs)
watch(
  () => props.modelValue,
  async (val) => {
    const ids = extractModelIds(Array.isArray(val) ? val : [])
    if (ids.length > 0) {
      try {
        const metadata = await systemFileApi.getMetadata(ids)
        // Store metadata
        metadata.forEach(file => {
          loadedFileMetadata.value.set(file.id, file)
        })
        // Update file list for display
        syncFileListFromMetadata(ids)
      } catch (error) {
        console.error('Failed to load file metadata:', error)
      }
      return
    }

    uploadFileList.value = []
  },
  { immediate: true }
)

// Sync file list from loaded metadata
function syncFileListFromMetadata(ids: string[]) {
  uploadFileList.value = ids
    .map((id: string, index: number) => {
      const meta = loadedFileMetadata.value.get(id)
      if (meta) {
        return {
          name: meta.fileName,
          url: meta.url,
          status: 'success',
          uid: index + 1,
          response: { success: true, data: meta }
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

function resolveFieldCode(): string {
  if (props.fieldCode) return props.fieldCode
  const fromField = props.field?.code || props.field?.fieldCode
  return typeof fromField === 'string' ? fromField : ''
}

function extractFileId(raw: unknown): string | null {
  if (!raw) return null
  if (typeof raw === 'string') return raw
  if (typeof raw !== 'object') return null
  const source = raw as Record<string, unknown>
  const candidate = source.id || source.fileId || source.value
  return typeof candidate === 'string' && candidate ? candidate : null
}

function extractModelIds(values: unknown[]): string[] {
  const seen = new Set<string>()
  const ids: string[] = []
  values.forEach((item) => {
    const id = extractFileId(item)
    if (!id || seen.has(id)) return
    seen.add(id)
    ids.push(id)
  })
  return ids
}

const httpRequest = async (options: UploadRequestOptions) => {
  const rawFile = options.file as File
  activeUploadCount.value += 1
  uploading.value = true
  errorMessage.value = ''

  try {
    const fileData = await systemFileApi.upload(rawFile, {
      objectCode: props.objectCode,
      instanceId: props.instanceId,
      fieldCode: resolveFieldCode(),
      onProgress: (percent: number) => {
        uploadProgress.value = Math.round(percent)
        options.onProgress?.({ percent } as any)
      }
    })

    loadedFileMetadata.value.set(fileData.id, fileData as unknown as FileItem)
    options.onSuccess?.({ success: true, data: fileData } as UploadSuccessResponse)
  } catch (error: any) {
    const uploadError = new Error(error?.message || t('common.messages.operationFailed')) as any
    uploadError.status = 0
    uploadError.method = 'post'
    uploadError.url = '/system/system-files/upload/'
    options.onError?.(uploadError)
  } finally {
    activeUploadCount.value = Math.max(0, activeUploadCount.value - 1)
    uploading.value = activeUploadCount.value > 0
  }
}

// Before upload validation
const beforeUpload: UploadProps['beforeUpload'] = (rawFile) => {
  const validation = validateFile(rawFile as File, {
    maxSize: props.maxSize,
    allowedTypes: props.allowedTypes
  })

  if (!validation.valid) {
    errorMessage.value = validation.error || t('common.messages.fileValidationFailed')
    ElMessage.error(errorMessage.value)
    return false
  }

  errorMessage.value = ''
  return true
}

// Handle file selection
const handleChange: UploadProps['onChange'] = (_uploadFile, uploadFiles) => {
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
  const payload = response as UploadSuccessResponse
  if (payload.success && payload.data) {
    const fileData: FileItem = payload.data
    loadedFileMetadata.value.set(fileData.id, fileData)
    updateModelValue()
    errorMessage.value = ''
  } else {
    file.status = 'fail'
    errorMessage.value = payload.message || t('common.messages.operationFailed')
  }
}

// Handle upload error
const handleError: UploadProps['onError'] = (error, file) => {
  file.status = 'fail'
  const normalized = error as Error
  errorMessage.value = `${t('common.messages.operationFailed')}: ${normalized.message || t('common.messages.unknownError')}`
  ElMessage.error(errorMessage.value)
}

// Handle file removal
const handleRemove: UploadProps['onRemove'] = (file) => {
  const targetUid = file.uid
  const index = uploadFileList.value.findIndex((f: UploadUserFile) => f.uid === targetUid)
  if (index > -1) {
    uploadFileList.value.splice(index, 1)
    updateModelValue()
  }
}

// Handle exceed max count
const handleExceed: UploadProps['onExceed'] = () => {
  ElMessage.warning(t('common.messages.maxFileCountExceeded', { count: props.maxCount }))
}

// Start manual upload
function startUpload() {
  if (!uploadRef.value) return

  // Validate all files before upload
  const readyFiles = uploadFileList.value.filter((f: UploadUserFile) => f.status === 'ready')
  const rawFiles = readyFiles
    .map((f: UploadUserFile) => f.raw)
    .filter((raw): raw is NonNullable<typeof raw> => Boolean(raw))
  const validation = validateFiles(
    rawFiles as unknown as File[],
    {
      maxCount: props.maxCount,
      maxSize: props.maxSize,
      allowedTypes: props.allowedTypes
    }
  )

  if (!validation.valid) {
    errorMessage.value = validation.error || t('common.messages.fileValidationFailed')
    ElMessage.error(errorMessage.value)
    return
  }

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
    .map((f: UploadUserFile) => {
      const response = f.response as { data?: { id?: string } } | undefined
      if (f.status === 'success' && response?.data?.id) return response.data.id
      const fallback = extractFileId((f as unknown as { response?: unknown }).response)
      return fallback || null
    })
    .filter((id): id is string => typeof id === 'string' && id.length > 0)

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
