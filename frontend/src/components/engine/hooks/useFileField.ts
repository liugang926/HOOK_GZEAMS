/**
 * useFileField Composable
 *
 * Common logic for file/image attachment fields in the dynamic form engine.
 * Provides unified file upload, metadata management, and display functionality
 * for AttachmentUpload, ImageField, and FileDisplayField components.
 *
 * Features:
 * - File upload with progress tracking
 * - File metadata loading and caching
 * - File type detection (image, PDF, etc.)
 * - File size formatting
 * - Download URL generation
 * - Context-aware upload (objectCode, instanceId, fieldCode)
 *
 * Reference: docs/plans/file_attachment_field/PRD.md
 */

import { ref, computed, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { systemFileApi, type SystemFile, validateFiles } from '@/api/systemFile'

/**
 * File upload context options
 */
export interface FileUploadContext {
  objectCode?: string
  instanceId?: string
  fieldCode?: string
}

/**
 * File upload options
 */
export interface FileUploadOptions {
  maxSize?: number // in bytes
  allowedTypes?: string[] // MIME types
  maxCount?: number
  autoUpload?: boolean
}

/**
 * File item interface for display
 */
export interface FileDisplayItem {
  id: string
  fileName: string
  fileSize: number
  fileType: string
  url: string
  thumbnailUrl?: string
  watermarkedUrl?: string
  width?: number
  height?: number
  isCompressed?: boolean
  createdAt?: string
}

/**
 * Upload state
 */
export interface UploadState {
  uploading: boolean
  progress: number
  error: string
}

/**
 * Composable return type
 */
export interface UseFileFieldReturn {
  // State
  files: Ref<FileDisplayItem[]>
  fileMetadataMap: Ref<Map<string, SystemFile>>
  uploadState: Ref<UploadState>

  // Computed
  hasFiles: Ref<boolean>
  imageFiles: Ref<FileDisplayItem[]>
  nonImageFiles: Ref<FileDisplayItem[]>

  // Methods
  loadFileMetadata: (fileIds: string[]) => Promise<void>
  uploadFile: (file: File, context?: FileUploadContext) => Promise<SystemFile | null>
  uploadFiles: (files: File[], context?: FileUploadContext) => Promise<SystemFile[]>
  deleteFile: (fileId: string) => Promise<void>
  downloadFile: (fileId: string) => string
  getDownloadUrl: (fileId: string) => string
  getFileUrl: (fileId: string) => string
  getThumbnailUrl: (fileId: string) => string

  // Utility methods
  isImageFile: (file: FileDisplayItem | SystemFile | File) => boolean
  isPdfFile: (file: FileDisplayItem | SystemFile | File) => boolean
  formatFileSize: (bytes: number) => string
  validateUpload: (file: File, options?: FileUploadOptions) => { valid: boolean; error?: string }

  // Sync methods
  syncFromFileIds: (fileIds: unknown) => Promise<void>
  getFileIds: () => string[]
  clearFiles: () => void
}

/**
 * useFileField Composable
 *
 * @param initialValue - Initial file IDs or file objects
 * @param uploadOptions - Upload validation options
 * @param uploadContext - Context for file uploads (objectCode, etc.)
 *
 * @example
 * ```ts
 * const {
 *   files,
 *   uploadFile,
 *   loadFileMetadata,
 *   isImageFile,
 *   formatFileSize
 * } = useFileField(
 *   ref(['file-id-1', 'file-id-2']),
 *   { maxSize: 10 * 1024 * 1024, maxCount: 5 },
 *   { objectCode: 'asset', instanceId: '123' }
 * )
 * ```
 */
export function useFileField(
  initialValue: Ref<unknown> = ref(null),
  uploadOptions: FileUploadOptions = {},
  uploadContext: FileUploadContext = {}
): UseFileFieldReturn {
  const { t } = useI18n()

  // State
  const files = ref<FileDisplayItem[]>([]) as Ref<FileDisplayItem[]>
  const fileMetadataMap = ref<Map<string, SystemFile>>(new Map())
  const uploadState = ref<UploadState>({
    uploading: false,
    progress: 0,
    error: ''
  })

  // Computed properties
  const hasFiles = computed(() => files.value.length > 0)

  const imageFiles = computed(() =>
    files.value.filter(f => isImageFile(f))
  )

  const nonImageFiles = computed(() =>
    files.value.filter(f => !isImageFile(f))
  )

  const extractFileId = (raw: unknown): string | null => {
    if (!raw) return null
    if (typeof raw === 'string') return raw
    if (typeof raw !== 'object') return null

    const source = raw as Record<string, unknown>
    const candidate = source.id || source.fileId || source.value
    return typeof candidate === 'string' && candidate ? candidate : null
  }

  const normalizeFileIds = (raw: unknown): string[] => {
    if (!raw) return []
    const values = Array.isArray(raw) ? raw : [raw]
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

  /**
   * Load file metadata from API
   */
  const loadFileMetadata = async (fileIds: string[]): Promise<void> => {
    if (!fileIds || fileIds.length === 0) {
      files.value = []
      return
    }

    // Filter out any non-string values
    const validIds = fileIds.filter(id => typeof id === 'string' && id)

    if (validIds.length === 0) {
      files.value = []
      return
    }

    try {
      const metadata = await systemFileApi.getMetadata(validIds)

      // Update metadata map
      metadata.forEach(file => {
        fileMetadataMap.value.set(file.id, file)
      })

      // Update files array
      files.value = metadata.map(toFileDisplayItem)
    } catch (error) {
      console.error('Failed to load file metadata:', error)
      ElMessage.error(t('common.messages.loadFailed'))
    }
  }

  /**
   * Upload a single file
   */
  const uploadFile = async (
    file: File,
    context?: FileUploadContext
  ): Promise<SystemFile | null> => {
    // Validate file
    const validation = validateUpload(file, uploadOptions)
    if (!validation.valid) {
      uploadState.value.error = validation.error || t('common.messages.operationFailed')
      ElMessage.error(uploadState.value.error)
      return null
    }

    uploadState.value.uploading = true
    uploadState.value.progress = 0
    uploadState.value.error = ''

    try {
      const fileData = await systemFileApi.upload(file, {
        objectCode: context?.objectCode || uploadContext.objectCode,
        instanceId: context?.instanceId || uploadContext.instanceId,
        fieldCode: context?.fieldCode || uploadContext.fieldCode,
        onProgress: (percent) => {
          uploadState.value.progress = percent
        }
      })

      if (!fileData?.id) {
        uploadState.value.error = t('common.messages.operationFailed')
        ElMessage.error(uploadState.value.error)
        return null
      }

      // Update metadata map
      fileMetadataMap.value.set(fileData.id, fileData)

      // Add to files array if not already present
      const existingIndex = files.value.findIndex(f => f.id === fileData.id)
      if (existingIndex === -1) {
        files.value.push(toFileDisplayItem(fileData))
      } else {
        files.value[existingIndex] = toFileDisplayItem(fileData)
      }

      uploadState.value.progress = 100
      ElMessage.success(t('common.messages.operationSuccess'))
      return fileData
    } catch (error: any) {
      uploadState.value.error = error.message || t('common.messages.operationFailed')
      ElMessage.error(uploadState.value.error)
      return null
    } finally {
      uploadState.value.uploading = false
    }
  }

  /**
   * Upload multiple files
   */
  const uploadFiles = async (
    fileList: File[],
    context?: FileUploadContext
  ): Promise<SystemFile[]> => {
    // Validate files
    const validation = validateFiles(fileList, uploadOptions)
    if (!validation.valid) {
      uploadState.value.error = validation.error || t('common.messages.operationFailed')
      ElMessage.error(uploadState.value.error)
      return []
    }

    const results: SystemFile[] = []
    uploadState.value.uploading = true
    uploadState.value.progress = 0

    for (let i = 0; i < fileList.length; i++) {
      const result = await uploadFile(fileList[i], context)
      if (result) {
        results.push(result)
      }
      uploadState.value.progress = Math.round(((i + 1) / fileList.length) * 100)
    }

    uploadState.value.uploading = false
    return results
  }

  /**
   * Delete a file
   */
  const deleteFile = async (fileId: string): Promise<void> => {
    try {
      await systemFileApi.delete(fileId)

      // Remove from metadata map
      fileMetadataMap.value.delete(fileId)

      // Remove from files array
      files.value = files.value.filter(f => f.id !== fileId)

      ElMessage.success(t('common.messages.deleteSuccess'))
    } catch (error) {
      console.error('Failed to delete file:', error)
      ElMessage.error(t('common.messages.deleteFailed'))
    }
  }

  /**
   * Get download URL for a file
   */
  const downloadFile = (fileId: string): string => {
    return systemFileApi.download(fileId)
  }

  /**
   * Get download URL alias
   */
  const getDownloadUrl = (fileId: string): string => {
    return downloadFile(fileId)
  }

  /**
   * Get file URL
   */
  const getFileUrl = (fileId: string): string => {
    const metadata = fileMetadataMap.value.get(fileId)
    return metadata?.url || downloadFile(fileId)
  }

  /**
   * Get thumbnail URL for a file
   */
  const getThumbnailUrl = (fileId: string): string => {
    const metadata = fileMetadataMap.value.get(fileId)
    return metadata?.thumbnailUrl || metadata?.url || downloadFile(fileId)
  }

  /**
   * Check if file is an image
   */
  const isImageFile = (file: FileDisplayItem | SystemFile | File): boolean => {
    if ('fileType' in file) {
      return file.fileType?.startsWith('image/') || false
    }
    if ('type' in file) {
      return file.type?.startsWith('image/') || false
    }
    if ('fileName' in file || 'name' in file) {
      const name = (file as FileDisplayItem).fileName || (file as File).name || ''
      const ext = name.split('.').pop()?.toLowerCase() || ''
      return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)
    }
    return false
  }

  /**
   * Check if file is a PDF
   */
  const isPdfFile = (file: FileDisplayItem | SystemFile | File): boolean => {
    if ('fileType' in file) {
      return file.fileType === 'application/pdf'
    }
    if ('type' in file) {
      return file.type === 'application/pdf'
    }
    if ('fileName' in file || 'name' in file) {
      const name = (file as FileDisplayItem).fileName || (file as File).name || ''
      return name.toLowerCase().endsWith('.pdf')
    }
    return false
  }

  /**
   * Format file size for display
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  /**
   * Validate file for upload
   */
  const validateUpload = (
    file: File,
    options?: FileUploadOptions
  ): { valid: boolean; error?: string } => {
    const opts = options || uploadOptions

    if (opts.maxSize && file.size > opts.maxSize) {
      return {
        valid: false,
        error: t('common.messages.operationFailed')
      }
    }

    if (opts.allowedTypes && opts.allowedTypes.length > 0) {
      const fileMime = file.type
      const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()

      const typeMatch = opts.allowedTypes.some(type => {
        if (type.endsWith('/*')) {
          const baseType = type.split('/')[0]
          return fileMime.startsWith(baseType + '/')
        }
        return fileMime === type || fileExt === type
      })

      if (!typeMatch) {
        return {
          valid: false,
          error: t('common.messages.operationFailed')
        }
      }
    }

    return { valid: true }
  }

  /**
   * Sync files from file IDs
   */
  const syncFromFileIds = async (fileIds: unknown): Promise<void> => {
    const validIds = normalizeFileIds(fileIds)
    if (!validIds.length) {
      files.value = []
      return
    }

    await loadFileMetadata(validIds)
  }

  /**
   * Get current file IDs
   */
  const getFileIds = (): string[] => {
    return files.value.map(f => f.id)
  }

  /**
   * Clear all files
   */
  const clearFiles = (): void => {
    files.value = []
    fileMetadataMap.value.clear()
  }

  // Convert SystemFile to FileDisplayItem
  function toFileDisplayItem(file: SystemFile): FileDisplayItem {
    return {
      id: file.id,
      fileName: file.fileName,
      fileSize: file.fileSize,
      fileType: file.fileType,
      url: file.url,
      thumbnailUrl: file.thumbnailUrl,
      watermarkedUrl: file.watermarkedUrl,
      width: file.width,
      height: file.height,
      isCompressed: file.isCompressed,
      createdAt: file.createdAt
    }
  }

  // Watch for initial value changes
  if (initialValue) {
    watch(
      initialValue,
      (newValue) => {
        syncFromFileIds(newValue)
      },
      { immediate: true }
    )
  }

  return {
    // State
    files,
    fileMetadataMap,
    uploadState,

    // Computed
    hasFiles,
    imageFiles,
    nonImageFiles,

    // Methods
    loadFileMetadata,
    uploadFile,
    uploadFiles,
    deleteFile,
    downloadFile,
    getDownloadUrl,
    getFileUrl,
    getThumbnailUrl,

    // Utility methods
    isImageFile,
    isPdfFile,
    formatFileSize,
    validateUpload,

    // Sync methods
    syncFromFileIds,
    getFileIds,
    clearFiles
  }
}

/**
 * Type guard to check if value is a FileDisplayItem
 */
export function isFileDisplayItem(value: any): value is FileDisplayItem {
  return (
    typeof value === 'object' &&
    typeof value.id === 'string' &&
    typeof value.fileName === 'string' &&
    typeof value.fileSize === 'number' &&
    typeof value.url === 'string'
  )
}

/**
 * Type guard to check if value is a SystemFile
 */
export function isSystemFile(value: any): value is SystemFile {
  return (
    typeof value === 'object' &&
    typeof value.id === 'string' &&
    typeof value.fileName === 'string' &&
    typeof value.filePath === 'string'
  )
}
