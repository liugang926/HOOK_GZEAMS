/**
 * Translation API client for i18n system.
 *
 * Provides methods for:
 * - Language management
 * - Translation CRUD operations
 * - Object translations
 * - Import/Export operations
 */

import request from '@/utils/request'
import { getStoredLocale, setStoredLocale } from '@/platform/i18n/localePreference'

export interface Language {
  id: string
  code: string
  name: string
  nativeName: string
  isDefault: boolean
  isActive: boolean
  sortOrder: number
  flagEmoji?: string
  locale?: string
  createdAt?: string
  updatedAt?: string
}

export interface Translation {
  id: string
  namespace?: string
  key?: string
  contentTypeModel?: string
  objectId?: string
  fieldName?: string
  languageCode: string
  text: string
  context?: string
  type?: string
  isSystem?: boolean
  createdAt?: string
  updatedAt?: string
}

export interface ObjectTranslations {
  [locale: string]: {
    [field: string]: string
  }
}

export interface TranslationStats {
  byLanguage: Array<{ language_code: string; count: number }>
  byNamespace: Array<{ namespace: string; count: number }>
  byType: Array<{ type: string; count: number }>
  systemVsUser: { system: number; user: number }
}

// ============================================================================
// Language API
// ============================================================================

export const languageApi = {
  /**
   * Get all languages
   */
  list: () => {
    return request.get<{ success: boolean; data: Language[] }>('/system/languages/')
  },

  /**
   * Get active languages only
   */
  getActive: () => {
    return request.get<{ success: boolean; data: Language[] }>('/system/languages/active/', {
      noAuth: true,
      silent: true,
    } as any)
  },

  /**
   * Get default language
   */
  getDefault: () => {
    return request.get<{ success: boolean; data: Language }>('/system/languages/default/')
  },

  /**
   * Create a new language
   */
  create: (data: Partial<Language>) => {
    return request.post<{ success: boolean; data: Language }>('/system/languages/', data)
  },

  /**
   * Update a language
   */
  update: (id: string, data: Partial<Language>) => {
    return request.put<{ success: boolean; data: Language }>(`/system/languages/${id}/`, data)
  },

  /**
   * Set a language as default
   */
  setDefault: (id: string) => {
    return request.post<{ success: boolean; data: Language; message: string }>(
      `/system/languages/${id}/set-default/`
    )
  },

  /**
   * Delete a language
   */
  delete: (id: string) => {
    return request.delete<{ success: boolean; message: string }>(`/system/languages/${id}/`)
  }
}

// ============================================================================
// Translation API
// ============================================================================

export const translationApi = {
  /**
   * Get translations with filtering
   */
  list: (params?: {
    namespace?: string
    key?: string
    language_code?: string
    type?: string
    is_system?: boolean
    content_type_model?: string
    object_id?: string
    field_name?: string
    page?: number
    page_size?: number
  }) => {
    return request.get<{ success: boolean; data: { count: number; results: Translation[] } }>(
      '/system/translations/',
      { params }
    )
  },

  /**
   * Get a single translation
   */
  get: (id: string) => {
    return request.get<{ success: boolean; data: Translation }>(`/system/translations/${id}/`)
  },

  /**
   * Create a new translation
   */
  create: (data: Partial<Translation>) => {
    return request.post<{ success: boolean; data: Translation }>('/system/translations/', data)
  },

  /**
   * Update a translation
   */
  update: (id: string, data: Partial<Translation>) => {
    return request.put<{ success: boolean; data: Translation }>(`/system/translations/${id}/`, data)
  },

  /**
   * Partial update a translation
   */
  partialUpdate: (id: string, data: Partial<Translation>) => {
    return request.patch<{ success: boolean; data: Translation }>(`/system/translations/${id}/`, data)
  },

  /**
   * Delete a translation
   */
  delete: (id: string) => {
    return request.delete<{ success: boolean; message: string }>(`/system/translations/${id}/`)
  },

  /**
   * Bulk create/update translations
   */
  bulk: (translations: Partial<Translation>[]) => {
    return request.post<{
      success: boolean
      message: string
      summary: { total: number; created: number; updated: number; failed: number }
      results: Array<{ id?: string; action: string; success: boolean; error?: string }>
    }>('/system/translations/bulk/', { translations })
  },

  /**
   * Get translations by namespace
   */
  getByNamespace: (namespace: string, languageCode?: string) => {
    return request.get<{
      success: boolean
      data: {
        namespace: string
        translations: Record<string, Record<string, string>>
      }
    }>(`/system/translations/namespace/${namespace}/`, {
      params: languageCode ? { language_code: languageCode } : undefined
    })
  },

  /**
   * Get translations for an object
   */
  getByObject: (contentType: string, objectId: string) => {
    return request.get<{
      success: boolean
      data: {
        content_type: string
        object_id: string
        translations: Record<string, Record<string, string>>
      }
    }>(`/system/translations/object/${contentType}/${objectId}/`)
  },

  /**
   * Set translations for an object
   */
  setObjectTranslations: (
    contentType: string,
    objectId: string,
    translations: ObjectTranslations
  ) => {
    return request.put<{
      success: boolean
      message: string
      data: {
        content_type: string
        object_id: string
        results: Array<{ locale: string; field: string; text: string; action: string }>
      }
    }>(`/system/translations/object/${contentType}/${objectId}/`, { translations })
  },

  /**
   * Export translations to CSV
   */
  export: (params: {
    language_code: string
    namespace?: string
    content_type?: string
  }) => {
    return request.get(`/system/translations/export/`, {
      params,
      responseType: 'blob'
    })
  },

  /**
   * Import translations from CSV
   */
  import: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<{
      success: boolean
      message: string
      data: {
        total: number
        summary: { created: number; updated: number; failed: number; errors: Array<{ row: number; error: string }> }
      }
    }>('/system/translations/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /**
   * Get translation statistics
   */
  getStats: () => {
    return request.get<{
      success: boolean
      data: {
        total: TranslationStats
      }
    }>('/system/translations/stats/')
  }
}

// ============================================================================
// Helper functions
// ============================================================================

/**
 * Get current user's language preference
 */
export const getCurrentLanguage = (): string => {
  return getStoredLocale()
}

/**
 * Set current language and persist to localStorage
 */
export const setCurrentLanguage = (langCode: string) => {
  setStoredLocale(langCode)

  // Update HTML lang attribute
  document.documentElement.lang = langCode.replace('-', '')
}

/**
 * Format language code to locale (e.g., 'zh-CN' -> 'zhCN')
 */
export const langToLocale = (langCode: string): string => {
  return langCode.replace('-', '')
}

/**
 * Format locale to language code (e.g., 'zhCN' -> 'zh-CN')
 */
export const localeToLang = (locale: string): string => {
  if (locale.length === 4) {
    return locale.slice(0, 2) + '-' + locale.slice(2).toUpperCase()
  }
  return locale
}
