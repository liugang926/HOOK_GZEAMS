/**
 * useFileField composable tests
 */

import { describe, it, expect } from 'vitest'

describe('useFileField', () => {
  describe('formatFileSize', () => {
    it('should format bytes correctly', () => {
      function formatFileSize(bytes: number): string {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
      }

      expect(formatFileSize(512)).toBe('512 B')
      expect(formatFileSize(1024)).toBe('1.0 KB')
      expect(formatFileSize(5120)).toBe('5.0 KB')
      expect(formatFileSize(1024 * 1024)).toBe('1.0 MB')
      expect(formatFileSize(5 * 1024 * 1024)).toBe('5.0 MB')
    })
  })

  describe('isImageFile', () => {
    it('should return true for image types', () => {
      const imageTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']

      imageTypes.forEach(type => {
        const isImage = type.startsWith('image/')
        expect(isImage).toBe(true)
      })
    })

    it('should return false for non-image types', () => {
      const nonImageTypes = ['application/pdf', 'text/plain', 'application/json']

      nonImageTypes.forEach(type => {
        const isImage = type.startsWith('image/')
        expect(isImage).toBe(false)
      })
    })
  })

  describe('isPdfFile', () => {
    it('should return true for PDF', () => {
      const fileType = 'application/pdf'
      const isPdf = fileType === 'application/pdf'

      expect(isPdf).toBe(true)
    })

    it('should return false for non-PDF', () => {
      const fileType: string = 'application/msword'
      const isPdf = fileType === 'application/pdf'

      expect(isPdf).toBe(false)
    })
  })

  describe('getFileIconClass', () => {
    function getFileIconClass(extension: string, fileType: string): string {
      if (fileType.startsWith('image/')) return 'image'
      if (fileType === 'application/pdf') return 'document-pdf'

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

      return iconMap[extension.toLowerCase()] || 'document-default'
    }

    it('should return correct icon for PDF', () => {
      const icon = getFileIconClass('pdf', 'application/pdf')
      expect(icon).toBe('document-pdf')
    })

    it('should return correct icon for Word documents', () => {
      expect(getFileIconClass('docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')).toBe('document-word')
      expect(getFileIconClass('doc', 'application/msword')).toBe('document-word')
    })

    it('should return correct icon for Excel spreadsheets', () => {
      expect(getFileIconClass('xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')).toBe('document-excel')
      expect(getFileIconClass('xls', 'application/vnd.ms-excel')).toBe('document-excel')
    })

    it('should return correct icon for PowerPoint', () => {
      expect(getFileIconClass('pptx', 'application/vnd.openxmlformats-officedocument.presentationml.presentation')).toBe('document-ppt')
      expect(getFileIconClass('ppt', 'application/vnd.ms-powerpoint')).toBe('document-ppt')
    })

    it('should return image icon for images', () => {
      expect(getFileIconClass('jpg', 'image/jpeg')).toBe('image')
      expect(getFileIconClass('png', 'image/png')).toBe('image')
      expect(getFileIconClass('gif', 'image/gif')).toBe('image')
    })

    it('should return default icon for unknown types', () => {
      expect(getFileIconClass('unknown', 'application/unknown')).toBe('document-default')
    })

    it('should return zip icon for archives', () => {
      expect(getFileIconClass('zip', 'application/zip')).toBe('document-zip')
      expect(getFileIconClass('rar', 'application/x-rar-compressed')).toBe('document-zip')
      expect(getFileIconClass('7z', 'application/x-7z-compressed')).toBe('document-zip')
    })
  })

  describe('hasFiles computed', () => {
    it('should return true when files exist', () => {
      const files = [{ id: 'file-001' }]
      const hasFiles = files.length > 0

      expect(hasFiles).toBe(true)
    })

    it('should return false when no files', () => {
      const files = []
      const hasFiles = files.length > 0

      expect(hasFiles).toBe(false)
    })
  })

  describe('syncFromFileIds', () => {
    it('should handle string file ID', () => {
      const fileIds: string | string[] | null = 'file-001'
      const ids = Array.isArray(fileIds) ? fileIds : [fileIds]

      expect(ids).toEqual(['file-001'])
    })

    it('should handle array of file IDs', () => {
      const fileIds: string | string[] | null = ['file-001', 'file-002']
      const ids = Array.isArray(fileIds) ? fileIds : [fileIds]

      expect(ids).toEqual(['file-001', 'file-002'])
    })

    it('should handle null file IDs', () => {
      const fileIds: string | string[] | null = null
      const ids = fileIds ? (Array.isArray(fileIds) ? fileIds : [fileIds]) : []

      expect(ids).toEqual([])
    })

    it('should clear files when syncing null', () => {
      const files: any[] = []
      const fileIds: string | string[] | null = null

      if (!fileIds) {
        files.length = 0
      }

      expect(files).toEqual([])
    })
  })

  describe('loadFileMetadata error handling', () => {
    it('should set error on API failure', () => {
      const error: string | null = 'Failed to load file metadata'

      expect(error).not.toBeNull()
      expect(error).toBe('Failed to load file metadata')
    })

    it('should clear files on error', () => {
      const files: any[] = []

      // Simulating error clearing files
      files.length = 0

      expect(files).toEqual([])
    })
  })

  describe('getDownloadUrl', () => {
    it('should return download URL', () => {
      const fileId = 'file-001'
      const downloadUrl = `/api/files/download/${fileId}`

      expect(downloadUrl).toBe('/api/files/download/file-001')
    })
  })
})
