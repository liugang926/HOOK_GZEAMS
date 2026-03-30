/**
 * Unit tests for i18n translation API client.
 */
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { translationApi, languageApi } from '@/api/translations'
import request from '@/utils/request'

// Mock the request module
vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('translationApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('list', () => {
    it('should fetch translations with params', async () => {
      const mockResponse = {
        success: true,
        data: {
          count: 2,
          results: [
            {
              id: '1',
              namespace: 'common',
              key: 'button.save',
              text: 'Save',
              languageCode: 'en-US'
            },
            {
              id: '2',
              namespace: 'common',
              key: 'button.cancel',
              text: 'Cancel',
              languageCode: 'en-US'
            }
          ]
        }
      }
      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await translationApi.list({ language_code: 'en-US', page: 1, page_size: 20 })

      expect(request.get).toHaveBeenCalledWith('/system/translations/', {
        params: { language_code: 'en-US', page: 1, page_size: 20 }
      })
      expect(result.data).toEqual(mockResponse.data)
    })
  })

  describe('create', () => {
    it('should create a new translation', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: '123',
          namespace: 'common',
          key: 'button.save',
          text: 'Save',
          languageCode: 'en-US',
          type: 'label'
        }
      }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const newTranslation = {
        languageCode: 'en-US',
        namespace: 'common',
        key: 'button.save',
        text: 'Save',
        type: 'label'
      }

      const result = await translationApi.create(newTranslation)

      expect(request.post).toHaveBeenCalledWith('/system/translations/', newTranslation)
      expect(result.data).toEqual(mockResponse.data)
    })

    it('should create object translation with GenericForeignKey', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: '123',
          contentTypeModel: 'businessobject',
          objectId: 'abc-123-def',
          fieldName: 'name',
          text: 'Asset',
          languageCode: 'en-US',
          type: 'object_field'
        }
      }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const newTranslation = {
        languageCode: 'en-US',
        contentTypeModel: 'businessobject',
        objectId: 'abc-123-def',
        fieldName: 'name',
        text: 'Asset',
        type: 'object_field'
      }

      const result = await translationApi.create(newTranslation)

      expect(result.data.objectId).toBe('abc-123-def')
    })
  })

  describe('update', () => {
    it('should update existing translation', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: '123',
          namespace: 'common',
          key: 'button.save',
          text: 'Save (Updated)',
          languageCode: 'en-US'
        }
      }
      vi.mocked(request.put).mockResolvedValue(mockResponse)

      const updates = { text: 'Save (Updated)' }

      const result = await translationApi.update('123', updates)

      expect(request.put).toHaveBeenCalledWith('/system/translations/123/', updates)
      expect(result.data.text).toBe('Save (Updated)')
    })
  })

  describe('delete', () => {
    it('should delete translation', async () => {
      vi.mocked(request.delete).mockResolvedValue({ success: true })

      await translationApi.delete('123')

      expect(request.delete).toHaveBeenCalledWith('/system/translations/123/')
    })
  })

  describe('bulk', () => {
    it('should bulk create translations', async () => {
      const mockResponse = {
        success: true,
        message: 'Bulk operation completed',
        summary: { total: 2, created: 2, updated: 0, failed: 0 },
        results: [
          { id: '1', action: 'created', success: true },
          { id: '2', action: 'created', success: true }
        ]
      }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const translations = [
        { languageCode: 'en-US', namespace: 'common', key: 'button.ok', text: 'OK' },
        { languageCode: 'zh-CN', namespace: 'common', key: 'button.ok', text: '确定' }
      ]

      const result = await translationApi.bulk(translations)

      expect(request.post).toHaveBeenCalledWith('/system/translations/bulk/', { translations })
      expect(result.summary.created).toBe(2)
    })
  })

  describe('export', () => {
    it('should export translations as CSV blob', async () => {
      const blob = new Blob(['namespace,key,text\ncommon,button.save,Save'], {
        type: 'text/csv'
      })
      vi.mocked(request.get).mockResolvedValue(blob)

      const result = await translationApi.export({ language_code: 'en-US' })

      expect(request.get).toHaveBeenCalledWith('/system/translations/export/', {
        params: { language_code: 'en-US' },
        responseType: 'blob'
      })
      expect(result).toBeInstanceOf(Blob)
    })
  })

  describe('import', () => {
    it('should import translations from CSV file', async () => {
      const mockResponse = {
        success: true,
        message: 'Import completed',
        data: {
          total: 7,
          summary: { created: 5, updated: 2, failed: 0, errors: [] }
        }
      }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const file = new File(['csv content'], 'translations.csv', { type: 'text/csv' })

      const result = await translationApi.import(file)

      expect(result.data.summary.created).toBe(5)
    })
  })

  describe('getStats', () => {
    it('should fetch translation statistics', async () => {
      const mockResponse = {
        success: true,
        data: {
          total: {
            byLanguage: [
              { language_code: 'zh-CN', count: 50 },
              { language_code: 'en-US', count: 100 }
            ],
            byNamespace: [
              { namespace: 'common', count: 30 },
              { namespace: 'asset', count: 20 }
            ],
            byType: [
              { type: 'label', count: 100 },
              { type: 'message', count: 50 }
            ],
            systemVsUser: { system: 120, user: 30 }
          }
        }
      }
      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await translationApi.getStats()

      expect(request.get).toHaveBeenCalledWith('/system/translations/stats/')
      expect(result.data.total.byLanguage).toHaveLength(2)
    })
  })

  describe('getByObject', () => {
    it('should fetch translations for specific object', async () => {
      const mockResponse = {
        success: true,
        data: {
          content_type: 'businessobject',
          object_id: 'abc-123',
          translations: {
            'en-US': { name: 'Asset', description: 'Test Asset' },
            'zh-CN': { name: '资产', description: '测试资产' }
          }
        }
      }
      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await translationApi.getByObject('businessobject', 'abc-123')

      expect(request.get).toHaveBeenCalledWith('/system/translations/object/businessobject/abc-123/')
      expect(result.data.translations['en-US'].name).toBe('Asset')
    })
  })
})

describe('languageApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('list', () => {
    it('should fetch all languages', async () => {
      const mockResponse = {
        success: true,
        data: [
          {
            id: '1',
            code: 'zh-CN',
            name: '简体中文',
            nativeName: '中文',
            flagEmoji: '🇨🇳',
            isDefault: true,
            isActive: true
          },
          {
            id: '2',
            code: 'en-US',
            name: 'English',
            nativeName: 'English',
            flagEmoji: '🇺🇸',
            isDefault: false,
            isActive: true
          }
        ]
      }
      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await languageApi.list()

      expect(request.get).toHaveBeenCalledWith('/system/languages/')
      expect(result.data).toHaveLength(2)
    })
  })

  describe('getActive', () => {
    it('should fetch only active languages', async () => {
      const mockResponse = {
        success: true,
        data: [
          {
            id: '1',
            code: 'zh-CN',
            name: '简体中文',
            isActive: true
          }
        ]
      }
      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await languageApi.getActive()

      expect(request.get).toHaveBeenCalledWith('/system/languages/active/', {
        noAuth: true,
        silent: true
      })
      expect(result.data).toHaveLength(1)
    })
  })

  describe('getDefault', () => {
    it('should fetch default language', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: '1',
          code: 'zh-CN',
          name: '简体中文',
          isDefault: true
        }
      }
      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await languageApi.getDefault()

      expect(request.get).toHaveBeenCalledWith('/system/languages/default/')
      expect(result.data.isDefault).toBe(true)
    })
  })

  describe('create', () => {
    it('should create new language', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: '123',
          code: 'ja-JP',
          name: 'Japanese',
          nativeName: '日本語',
          flagEmoji: '🇯🇵'
        }
      }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const newLanguage = {
        code: 'ja-JP',
        name: 'Japanese',
        nativeName: '日本語',
        flagEmoji: '🇯🇵',
        isActive: true,
        sortOrder: 3
      }

      const result = await languageApi.create(newLanguage)

      expect(request.post).toHaveBeenCalledWith('/system/languages/', newLanguage)
      expect(result.data.code).toBe('ja-JP')
    })
  })

  describe('update', () => {
    it('should update language', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: '123',
          code: 'en-US',
          name: 'English (Updated)'
        }
      }
      vi.mocked(request.put).mockResolvedValue(mockResponse)

      const updates = { name: 'English (Updated)' }

      const result = await languageApi.update('123', updates)

      expect(request.put).toHaveBeenCalledWith('/system/languages/123/', updates)
      expect(result.data.name).toBe('English (Updated)')
    })
  })

  describe('setDefault', () => {
    it('should set language as default', async () => {
      vi.mocked(request.post).mockResolvedValue({ success: true, message: 'Default language updated' })

      await languageApi.setDefault('123')

      expect(request.post).toHaveBeenCalledWith('/system/languages/123/set-default/')
    })
  })

  describe('delete', () => {
    it('should delete language', async () => {
      vi.mocked(request.delete).mockResolvedValue({ success: true, message: 'Language deleted' })

      await languageApi.delete('123')

      expect(request.delete).toHaveBeenCalledWith('/system/languages/123/')
    })
  })
})
