<template>
  <div class="image-field">
    <!-- Empty state -->
    <div
      v-if="!hasImage"
      class="empty-state"
    >
      <el-upload
        ref="uploadRef"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :show-file-list="false"
        :before-upload="beforeUpload"
        :on-success="handleSuccess"
        :on-error="handleError"
        :disabled="disabled"
        accept="image/*"
        :drag="dragUpload"
        class="upload-container"
      >
        <div
          v-if="dragUpload"
          class="upload-drag-area"
        >
          <el-icon
            class="upload-icon"
            :size="48"
          >
            <Picture />
          </el-icon>
          <div class="upload-text">
            {{ $t('fields.dragImageHere') }} <em>{{ $t('fields.clickToUpload') }}</em>
          </div>
          <div
            v-if="hint"
            class="upload-hint"
          >
            {{ hint }}
          </div>
          <div
            v-if="maxSize"
            class="upload-limit"
          >
            {{ $t('fields.maxSize') }}: {{ formatFileSize(maxSize) }}
          </div>
        </div>
        <el-button
          v-else
          type="primary"
          :disabled="disabled"
        >
          <el-icon><Upload /></el-icon>
          {{ buttonText || $t('fields.uploadImage') }}
        </el-button>
      </el-upload>
    </div>

    <!-- Image display -->
    <div
      v-else
      class="image-display"
    >
      <div class="image-preview-container">
        <!-- Thumbnail image -->
        <img
          :src="thumbnailUrl"
          :alt="currentImage?.fileName || 'Uploaded image'"
          class="image-thumbnail"
          @click="previewImage"
        >

        <!-- Image info overlay -->
        <div
          v-if="showInfo"
          class="image-info"
        >
          <span v-if="currentImage?.width">{{ currentImage.width }}x{{ currentImage.height }}</span>
          <span v-if="currentImage?.fileSize">{{ formatFileSize(currentImage.fileSize) }}</span>
        </div>

        <!-- Action buttons -->
        <div
          v-if="!disabled"
          class="image-actions"
        >
          <el-button-group>
            <el-button
              size="small"
              @click="previewImage"
            >
              <el-icon><ZoomIn /></el-icon>
            </el-button>
            <el-button
              size="small"
              @click="editImage"
            >
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="removeImage"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-button-group>
        </div>
      </div>
    </div>

    <!-- Image preview dialog -->
    <el-dialog
      v-model="showPreview"
      :title="$t('fields.imagePreview')"
      :width="800"
      append-to-body
    >
      <div class="preview-container">
        <img
          :src="fullImageUrl"
          alt="Full size preview"
        >
      </div>
      <div
        v-if="currentImage"
        class="preview-meta"
      >
        <p><strong>{{ $t('fields.filename') }}:</strong> {{ currentImage.fileName }}</p>
        <p><strong>{{ $t('fields.dimensions') }}:</strong> {{ currentImage.width }}x{{ currentImage.height }}px</p>
        <p><strong>{{ $t('fields.size') }}:</strong> {{ formatFileSize(currentImage.fileSize) }}</p>
        <p v-if="currentImage.isCompressed">
          <strong>{{ $t('fields.compressed') }}:</strong> {{ $t('fields.yes') }}
        </p>
      </div>
    </el-dialog>

    <!-- Image crop dialog -->
    <el-dialog
      v-model="showCrop"
      :title="$t('fields.editImage')"
      :width="700"
      append-to-body
      @closed="closeCropDialog"
    >
      <div
        v-if="cropImageUrl"
        class="crop-container"
      >
        <vue-cropper
          ref="cropperRef"
          :src="cropImageUrl"
          :aspect-ratio="aspectRatio"
          :auto-crop-area="1"
          :view-mode="1"
          :background="false"
          :responsive="true"
        />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCrop = false">{{ $t('actions.cancel') }}</el-button>
          <el-button
            type="primary"
            @click="applyCrop"
          >{{ $t('fields.apply') }}</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { UploadInstance } from 'element-plus'
import {
  Picture,
  Upload,
  ZoomIn,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import { systemFileApi, type SystemFile } from '@/api/systemFile'
import VueCropper from 'vue-cropperjs'
import { useFileField, type FileDisplayItem, type FileUploadContext } from '@/composables'

const { t } = useI18n()

interface ImageFieldProps {
  modelValue: string | string[] | null
  field?: any
  disabled?: boolean
  // Upload options
  maxSize?: number // in bytes
  dragUpload?: boolean
  buttonText?: string
  hint?: string
  // Display options
  showInfo?: boolean
  // Crop options
  enableCrop?: boolean
  aspectRatio?: number // NaN = free, 1 = square, 16/9 = wide
  // Object context
  objectCode?: string
  instanceId?: string
  fieldCode?: string
}

const props = withDefaults(defineProps<ImageFieldProps>(), {
  disabled: false,
  dragUpload: true,
  buttonText: 'Upload Image',
  showInfo: true,
  enableCrop: false,
  aspectRatio: NaN
})

const emit = defineEmits<{
  'update:modelValue': [value: string | string[] | null]
  'change': [value: string | string[] | null, file: SystemFile | null]
}>()

const uploadRef = ref<UploadInstance>()
const cropperRef = ref<InstanceType<typeof VueCropper>>()

const showPreview = ref(false)
const showCrop = ref(false)
const cropImageUrl = ref('')

// File upload context for useFileField composable
const uploadContext: FileUploadContext = {
  objectCode: props.objectCode,
  instanceId: props.instanceId,
  fieldCode: props.fieldCode
}

// Use the common useFileField composable for file handling
const initialValue = computed(() => {
  if (!props.modelValue) return null
  // Convert string to array for composable, then back to single string for image
  const id = Array.isArray(props.modelValue) ? props.modelValue[0] : props.modelValue
  return id ? [id] : null
})

const {
  files,
  hasFiles,
  uploadFile,
  loadFileMetadata,
  formatFileSize,
  getThumbnailUrl,
  getFileUrl,
  uploadState
} = useFileField(initialValue, { maxSize: props.maxSize }, uploadContext)

// Current image (single file from files array)
const currentImage = computed(() => {
  return files.value.length > 0 ? files.value[0] : null
})

// Check if has image
const hasImage = computed(() => hasFiles.value)

// Thumbnail URL
const thumbnailUrl = computed(() => {
  if (currentImage.value) {
    return getThumbnailUrl(currentImage.value.id)
  }
  return ''
})

// Full image URL
const fullImageUrl = computed(() => {
  if (currentImage.value) {
    return getFileUrl(currentImage.value.id)
  }
  return ''
})

// Upload URL (for el-upload component)
const uploadUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL || '/api'}/system/system-files/upload/`
})

// Upload headers with auth token (for el-upload component)
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  return {
    'Authorization': token ? `Bearer ${token}` : ''
  }
})

// Load image from model value using the composable
watch(
  () => props.modelValue,
  async (val) => {
    if (!val) {
      // Clear files
      return
    }

    const id = Array.isArray(val) ? val[0] : val
    if (id && typeof id === 'string') {
      await loadFileMetadata([id])
    }
  },
  { immediate: true }
)

// Before upload validation (for el-upload component)
function beforeUpload(file: File): boolean {
  // Check file type
  if (!file.type.startsWith('image/')) {
    ElMessage.error(t('fields.onlyImageAllowed'))
    return false
  }

  // Check file size
  if (props.maxSize && file.size > props.maxSize) {
    const maxSizeMB = Math.round(props.maxSize / 1024 / 1024 * 100) / 100
    ElMessage.error(`${t('fields.imageSizeExceeds')} ${maxSizeMB}MB.`)
    return false
  }

  return true
}

// Handle upload success (for el-upload component)
function handleSuccess(response: any): void {
  if (response.success && response.data) {
    const fileData: SystemFile = response.data
    emit('update:modelValue', fileData.id)
    emit('change', fileData.id, fileData)
    // File is already added to files array by useFileField composable
  } else {
    ElMessage.error(response.message || t('fields.uploadFailed'))
  }
}

// Handle upload error
function handleError(error: any): void {
  console.error('Upload error:', error)
  ElMessage.error(t('fields.uploadFailed'))
}

// Preview image
function previewImage(): void {
  showPreview.value = true
}

// Edit/crop image
function editImage(): void {
  if (!props.enableCrop) {
    ElMessage.info(t('fields.cropNotEnabled'))
    return
  }
  if (currentImage.value?.url) {
    cropImageUrl.value = currentImage.value.url
    showCrop.value = true
  }
}

// Apply crop (uses composable for upload)
async function applyCrop(): Promise<void> {
  if (!cropperRef.value) return

  // Get cropped canvas
  const canvas = cropperRef.value.getCropper()?.getCroppedCanvas()
  if (!canvas) {
    ElMessage.error(t('fields.imageProcessFailed'))
    return
  }

  // Convert to blob and upload
  canvas.toBlob(async (blob) => {
    if (!blob) return

    const file = new File([blob], currentImage.value?.fileName || 'cropped-image.jpg', {
      type: 'image/jpeg'
    })

    // Upload the cropped image using composable
    const result = await uploadFile(file, {
      objectCode: props.objectCode,
      instanceId: props.instanceId,
      fieldCode: props.fieldCode
    })

    if (result) {
      emit('update:modelValue', result.id)
      emit('change', result.id, result)
      showCrop.value = false
    }
  }, 'image/jpeg', 0.9)
}

// Close crop dialog
function closeCropDialog(): void {
  cropImageUrl.value = ''
}

// Remove image (clears files via composable)
function removeImage(): void {
  // The files array will be cleared when modelValue is updated
  emit('update:modelValue', null)
  emit('change', null, null)
}

// Expose methods
defineExpose({
  previewImage,
  editImage,
  removeImage,
  triggerUpload: () => uploadRef.value?.handleClick(),
  // Expose composable methods for external use
  files,
  uploadFile,
  loadFileMetadata
})
</script>

<style scoped lang="scss">
.image-field {
  width: 100%;
}

.empty-state {
  .upload-container {
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

  .upload-limit {
    margin-top: 4px;
    font-size: 11px;
    color: var(--el-text-color-placeholder);
  }
}

.image-display {
  .image-preview-container {
    position: relative;
    display: inline-block;
    max-width: 100%;
  }

  .image-thumbnail {
    max-width: 200px;
    max-height: 200px;
    border-radius: 4px;
    cursor: pointer;
    object-fit: cover;
    transition: transform 0.2s;

    &:hover {
      transform: scale(1.02);
    }
  }

  .image-info {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 4px 8px;
    background: rgba(0, 0, 0, 0.6);
    color: white;
    font-size: 11px;
    border-radius: 0 0 4px 4px;
    display: flex;
    justify-content: space-between;
  }

  .image-actions {
    position: absolute;
    top: 4px;
    right: 4px;
    opacity: 0;
    transition: opacity 0.2s;

    .image-preview-container:hover & {
      opacity: 1;
    }
  }
}

.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;

  img {
    max-width: 100%;
    max-height: 500px;
    object-fit: contain;
  }
}

.preview-meta {
  margin-top: 16px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  font-size: 13px;

  p {
    margin: 4px 0;
  }
}

.crop-container {
  height: 400px;

  :deep(.vue-cropper) {
    height: 100%;
  }
}
</style>
