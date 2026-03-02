/**
 * System File API
 *
 * Provides file upload, download, and management functionality
 * for dynamic object file/attachment fields.
 *
 * Reference: docs/plans/file_attachment_field/PRD.md
 */

import request from '@/utils/request'

// =============================================================================
// Type Definitions
// =============================================================================

/**
 * System file metadata
 * Backend returns camelCase via djangorestframework-camel-case
 */
export interface SystemFile {
    id: string
    fileName: string
    filePath: string
    fileSize: number
    fileType: string
    fileExtension: string
    url: string
    thumbnailUrl?: string
    thumbnailPath?: string
    watermarkedUrl?: string
    watermarkedPath?: string
    width?: number
    height?: number
    isCompressed?: boolean
    originalFileId?: string
    objectCode?: string
    instanceId?: string
    fieldCode?: string
    bizType?: string
    bizId?: string
    description?: string
    fileHash?: string
    createdAt: string
    updatedAt: string
}

/**
 * Upload options
 */
export interface UploadOptions {
    objectCode?: string
    instanceId?: string
    fieldCode?: string
    description?: string
    onProgress?: (percent: number) => void
}

/**
 * Upload response
 */
export interface UploadResponse {
    success: boolean
    data: SystemFile
    message?: string
    isDuplicate?: boolean
}

/**
 * Batch operation response
 */
export interface BatchOperationResponse {
    success: boolean
    message: string
    summary: {
        total: number
        succeeded: number
        failed: number
    }
    results: Array<{
        id: string
        success: boolean
        error?: string
    }>
}

// =============================================================================
// System File API
// =============================================================================

export const systemFileApi = {
    /**
     * Upload a file
     * POST /api/system/system-files/upload/
     */
    upload: (file: File, options?: UploadOptions): Promise<SystemFile> => {
        const formData = new FormData()
        formData.append('file', file)

        if (options?.objectCode) {
            formData.append('object_code', options.objectCode)
        }
        if (options?.instanceId) {
            formData.append('instance_id', options.instanceId)
        }
        if (options?.fieldCode) {
            formData.append('field_code', options.fieldCode)
        }
        if (options?.description) {
            formData.append('description', options.description)
        }

        return request<SystemFile>({
            url: '/system/system-files/upload/',
            method: 'post',
            data: formData,
            headers: {
                'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: (progressEvent) => {
                if (options?.onProgress && progressEvent.total) {
                    const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                    options.onProgress(percent)
                }
            }
        })
    },

    /**
     * Upload multiple files
     * POST /api/system/system-files/upload/ (called multiple times)
     */
    uploadMultiple: (files: File[], options?: UploadOptions): Promise<SystemFile[]> => {
        const uploads = files.map(file => systemFileApi.upload(file, options))
        return Promise.all(uploads)
    },

    /**
     * Get file metadata by ID
     * GET /api/system/system-files/{id}/
     */
    get: (id: string): Promise<SystemFile> => {
        return request<SystemFile>({
            url: `/system/system-files/${id}/`,
            method: 'get'
        })
    },

    /**
     * Alias for get() - for backwards compatibility
     */
    getFile: (id: string): Promise<SystemFile> => systemFileApi.get(id),

    /**
     * Get metadata for multiple files
     * GET /api/system/system-files/metadata/?ids=xxx,yyy
     */
    getMetadata: (ids: string[]): Promise<SystemFile[]> => {
        return request<SystemFile[]>({
            url: '/system/system-files/metadata/',
            method: 'get',
            params: {
                ids: ids.join(',')
            }
        })
    },

    /**
     * List files with pagination and filters
     * GET /api/system/system-files/
     */
    list: (params?: {
        page?: number
        pageSize?: number
        objectCode?: string
        instanceId?: string
        fieldCode?: string
        search?: string
    }): Promise<{
        count: number
        next: string | null
        previous: string | null
        results: SystemFile[]
    }> => {
        return request({
            url: '/system/system-files/',
            method: 'get',
            params
        })
    },

    /**
     * Download a file
     * GET /api/system/system-files/{id}/download/
     * Returns a blob URL for download
     */
    download: (id: string): string => {
        return `${import.meta.env.VITE_API_BASE_URL || '/api'}/system/system-files/${id}/download/`
    },

    /**
     * Get download URL for a file (for use in href/links)
     */
    getDownloadUrl: (id: string): string => {
        return systemFileApi.download(id)
    },

    /**
     * Get thumbnail URL for an image file
     * Uses the download endpoint (thumbnail is provided as metadata field, not a separate API action).
     */
    getThumbnailUrl: (id: string): string => {
        const apiBase = import.meta.env.VITE_API_BASE_URL || '/api'
        return `${apiBase}/system/system-files/${id}/download/`
    },

    /**
     * Get file view URL (for displaying images)
     * Uses thumbnail for images, regular download for other files
     */
    getFileUrl: (id: string): string => {
        const apiBase = import.meta.env.VITE_API_BASE_URL || '/api'
        return `${apiBase}/system/system-files/${id}/download/`
    },

    /**
     * Delete a file (soft delete)
     * DELETE /api/system/system-files/{id}/
     */
    delete: (id: string): Promise<void> => {
        return request({
            url: `/system/system-files/${id}/`,
            method: 'delete'
        })
    },

    /**
     * Batch delete files
     * POST /api/system/system-files/batch_delete/
     */
    batchDelete: (ids: string[]): Promise<BatchOperationResponse> => {
        return request<BatchOperationResponse>({
            url: '/system/system-files/batch_delete/',
            method: 'post',
            data: { ids }
        })
    },

    /**
     * Add watermark to an image file
     * POST /api/system/system-files/{id}/add_watermark/
     */
    addWatermark: (
        id: string,
        options?: {
            text?: string
            position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center'
            opacity?: number
        }
    ): Promise<{
        success: boolean
        data: {
            fileId: string
            watermarkedPath: string
            width: number
            height: number
            file?: SystemFile
        }
    }> => {
        return request({
            url: `/system/system-files/${id}/add_watermark/`,
            method: 'post',
            data: {
                text: options?.text,
                position: options?.position || 'bottom-right',
                opacity: options?.opacity || 128
            }
        })
    },

    /**
     * Download watermarked version of an image
     * GET /api/system/system-files/{id}/download_watermarked/
     * Returns a blob URL for download
     */
    downloadWatermarked: (id: string): string => {
        return `${import.meta.env.VITE_API_BASE_URL || '/api'}/system/system-files/${id}/download_watermarked/`
    },

    /**
     * Batch download multiple files as ZIP
     * POST /api/system/system-files/batch_download/
     * Returns a blob URL for download
     */
    batchDownload: (ids: string[], zipName?: string): Promise<Blob> => {
        return request<Blob>({
            url: '/system/system-files/batch_download/',
            method: 'post',
            data: { ids, zip_name: zipName },
            responseType: 'blob'
        })
    },

    /**
     * Get batch download URL (for direct download via hidden iframe)
     */
    getBatchDownloadUrl: (ids: string[], zipName?: string): string => {
        const apiBase = import.meta.env.VITE_API_BASE_URL || '/api'
        const params = new URLSearchParams()
        params.append('ids', ids.join(','))
        if (zipName) {
            params.append('zip_name', zipName)
        }
        return `${apiBase}/system/system-files/batch_download/?${params.toString()}`
    }
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

/**
 * Check if file is an image
 */
export function isImageFile(file: SystemFile | File): boolean {
    const fileName = 'fileName' in file ? file.fileName : file.name
    const fileType = 'fileType' in file ? file.fileType : file.type
    return fileType.startsWith('image/') || /\.(jpg|jpeg|png|gif|bmp|webp|svg)$/i.test(fileName)
}

/**
 * Check if file is a PDF
 */
export function isPdfFile(file: SystemFile | File): boolean {
    const fileType = 'fileType' in file ? file.fileType : file.type
    return fileType === 'application/pdf'
}

/**
 * Get file icon class based on file type
 */
export function getFileIconClass(file: SystemFile | File): string {
    const fileName = 'fileName' in file ? file.fileName : file.name
    const ext = fileName.split('.').pop()?.toLowerCase() || ''

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

/**
 * Validate file against constraints
 */
export interface FileValidationOptions {
    maxSize?: number // in bytes
    allowedTypes?: string[] // MIME types
    maxCount?: number
}

export interface FileValidationResult {
    valid: boolean
    error?: string
}

export function validateFile(
    file: File,
    options: FileValidationOptions
): FileValidationResult {
    // Check file size
    if (options.maxSize && file.size > options.maxSize) {
        const maxSizeMB = Math.round(options.maxSize / 1024 / 1024 * 100) / 100
        return {
            valid: false,
            error: `File size exceeds ${maxSizeMB}MB limit.`
        }
    }

    // Check file type
    if (options.allowedTypes && options.allowedTypes.length > 0) {
        const fileMime = file.type
        const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()

        const typeMatch = options.allowedTypes.some(type => {
            if (type.endsWith('/*')) {
                const baseType = type.split('/')[0]
                return fileMime.startsWith(baseType + '/')
            }
            return fileMime === type || fileExt === type
        })

        if (!typeMatch) {
            return {
                valid: false,
                error: `File type not allowed. Allowed types: ${options.allowedTypes.join(', ')}`
            }
        }
    }

    return { valid: true }
}

/**
 * Validate multiple files
 */
export function validateFiles(
    files: File[],
    options: FileValidationOptions
): FileValidationResult {
    if (options.maxCount && files.length > options.maxCount) {
        return {
            valid: false,
            error: `Maximum ${options.maxCount} file(s) allowed.`
        }
    }

    for (const file of files) {
        const result = validateFile(file, options)
        if (!result.valid) {
            return result
        }
    }

    return { valid: true }
}
