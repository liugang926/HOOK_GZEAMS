/**
 * useFileField - Composable for file/attachment field handling
 *
 * Provides unified file handling for both editing and display modes.
 * Handles file metadata loading, URL generation, and file type detection.
 *
 * Reference: docs/plans/file_attachment_field/PRD.md
 */

import { ref, computed, type Ref } from 'vue'
import { systemFileApi, type SystemFile, formatFileSize as formatFileSizeUtil } from '@/api/systemFile'

/**
 * File display item interface
 */
export interface FileDisplayItem {
  id: string
  fileName: string
  filePath: string
  fileSize: number
  fileType: string
  fileExtension: string
  url?: string
  thumbnailUrl?: string
  createdAt?: string
}

/**
 * Composable for file field handling
 *
 * @param fileId - Ref to file ID (optional, can be loaded later)
 *
 * @returns File field state and methods
 */
export function useFileField(fileId?: Ref<string | null>) {
  // File metadata state
  const files = ref<FileDisplayItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed: has files
  const hasFiles = computed(() => files.value.length > 0)

  /**
   * Load file metadata from API
   */
  async function loadFileMetadata(fileIds: string[]): Promise<void> {
    if (!fileIds || fileIds.length === 0) {
      files.value = []
      return
    }

    loading.value = true
    error.value = null

    try {
      const result = await systemFileApi.getMetadata(fileIds)
      files.value = result.map(f => ({
        id: f.id,
        fileName: f.fileName,
        filePath: f.filePath,
        fileSize: f.fileSize,
        fileType: f.fileType,
        fileExtension: f.fileExtension,
        url: f.url,
        thumbnailUrl: f.thumbnailUrl,
        createdAt: f.createdAt
      }))
    } catch (err: any) {
      console.error('Failed to load file metadata:', err)
      error.value = err.message || 'Failed to load file metadata'
      files.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * Load single file metadata
   */
  async function loadSingleFile(id: string): Promise<void> {
    return loadFileMetadata([id])
  }

  /**
   * Sync files from file IDs (for v-model binding)
   */
  async function syncFromFileIds(fileIds: string | string[] | null): Promise<void> {
    if (!fileIds) {
      files.value = []
      return
    }
    const ids = Array.isArray(fileIds) ? fileIds : [fileIds]
    await loadFileMetadata(ids)
  }

  /**
   * Get download URL for a file
   */
  function getDownloadUrl(fileId: string): string {
    return systemFileApi.download(fileId)
  }

  /**
   * Check if file is an image
   */
  function isImageFile(file: FileDisplayItem | SystemFile): boolean {
    const fileType = file.fileType
    return fileType.startsWith('image/')
  }

  /**
   * Check if file is a PDF
   */
  function isPdfFile(file: FileDisplayItem | SystemFile): boolean {
    return file.fileType === 'application/pdf'
  }

  /**
   * Format file size for display
   */
  function formatFileSize(bytes: number): string {
    return formatFileSizeUtil(bytes)
  }

  /**
   * Get file icon class based on file type
   */
  function getFileIconClass(file: FileDisplayItem | SystemFile): string {
    const ext = file.fileExtension.toLowerCase()
    const iconMap: Record<string, string> = {
      'pdf': 'document-pdf',
      'doc': 'document-word',
      'docx': 'document-word',
      'xls': 'document-excel',
      'xlsx': 'document-excel',
      'ppt': 'document-ppt',
      'pptx': 'document-ppt',
      'txt': 'document-text',
      'zip': 'document-zip',
      'rar': 'document-zip',
      '7z': 'document-zip'
    }
    if (isImageFile(file)) return 'image'
    if (isPdfFile(file)) return iconMap['pdf']
    return iconMap[ext] || 'document-default'
  }

  // Load file on mount if fileId provided
  if (fileId?.value) {
    loadSingleFile(fileId.value)
  }

  return {
    // State
    files,
    loading,
    error,
    hasFiles,
    // Methods
    loadFileMetadata,
    loadSingleFile,
    syncFromFileIds,
    getDownloadUrl,
    isImageFile,
    isPdfFile,
    formatFileSize,
    getFileIconClass
  }
}

// Export types
export type { SystemFile }
