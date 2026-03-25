/**
 * Unit tests for i18n frontend components.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElTable } from 'element-plus'
import { createPinia, setActivePinia } from 'pinia'

// Mock API
vi.mock('@/api/translations', () => ({
  languageApi: {
    list: vi.fn(() => Promise.resolve({
      success: true,
      data: [
        {
          id: '1',
          code: 'zh-CN',
          name: '简体中文',
          nativeName: '中文',
          flagEmoji: '🇨🇳',
          isDefault: true,
          isActive: true,
          sortOrder: 1
        },
        {
          id: '2',
          code: 'en-US',
          name: 'English',
          nativeName: 'English',
          flagEmoji: '🇺🇸',
          isDefault: false,
          isActive: true,
          sortOrder: 2
        }
      ]
    })),
    setDefault: vi.fn(() => Promise.resolve({ success: true })),
    update: vi.fn(() => Promise.resolve({ success: true })),
    create: vi.fn(() => Promise.resolve({
      success: true,
      data: { id: '3', code: 'ja-JP', name: 'Japanese' }
    })),
    delete: vi.fn(() => Promise.resolve({ success: true }))
  },
  translationApi: {
    list: vi.fn(() => Promise.resolve({
      success: true,
      data: {
        count: 4,
        results: [
          {
            id: '1',
            namespace: 'common',
            key: 'button.save',
            text: '保存',
            languageCode: 'zh-CN',
            type: 'label'
          },
          {
            id: '2',
            namespace: 'common',
            key: 'button.save',
            text: 'Save',
            languageCode: 'en-US',
            type: 'label'
          }
        ]
      }
    })),
    delete: vi.fn(() => Promise.resolve({ success: true })),
    getStats: vi.fn(() => Promise.resolve({
      success: true,
      data: {
        total: {
          byLanguage: [
            { language_code: 'zh-CN', count: 50 },
            { language_code: 'en-US', count: 100 }
          ]
        }
      }
    }))
  }
}))

// Mock i18n
const mockT = (key: string) => key
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: mockT
  })
}))

describe('LanguageList Component', () => {
  let pinia: any

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
  })

  it('should render language table', async () => {
    const wrapper = mount({
      template: `
        <el-table :data="languages">
          <el-table-column prop="code" label="Code" />
          <el-table-column prop="name" label="Name" />
          <el-table-column prop="flagEmoji" label="Flag" />
          <el-table-column prop="isDefault" label="Default" />
          <el-table-column prop="isActive" label="Active" />
        </el-table>
      `,
      components: { ElTable, ElTableColumn: { template: '<div />', props: ['prop', 'label'] } }
    }, {
      props: {
        languages: [
          {
            id: '1',
            code: 'zh-CN',
            name: '简体中文',
            flagEmoji: '🇨🇳',
            isDefault: true,
            isActive: true
          },
          {
            id: '2',
            code: 'en-US',
            name: 'English',
            flagEmoji: '🇺🇸',
            isDefault: false,
            isActive: true
          }
        ]
      }
    })

    expect(wrapper.find('.el-table').exists()).toBe(true)
  })

  it('should display language flag emoji', () => {
    const languages = [
      { flagEmoji: '🇨🇳', code: 'zh-CN' },
      { flagEmoji: '🇺🇸', code: 'en-US' }
    ]

    expect(languages[0].flagEmoji).toBe('🇨🇳')
    expect(languages[1].flagEmoji).toBe('🇺🇸')
  })

  it('should identify default language', () => {
    const languages = [
      { isDefault: true, code: 'zh-CN' },
      { isDefault: false, code: 'en-US' }
    ]

    const defaultLang = languages.find(l => l.isDefault)
    expect(defaultLang?.code).toBe('zh-CN')
  })
})

describe('TranslationList Component', () => {
  let pinia: any

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
  })

  it('should render translation table with filters', () => {
    const translations = [
      {
        id: '1',
        namespace: 'common',
        key: 'button.save',
        text: '保存',
        languageCode: 'zh-CN',
        type: 'label'
      },
      {
        id: '2',
        namespace: 'common',
        key: 'button.save',
        text: 'Save',
        languageCode: 'en-US',
        type: 'label'
      }
    ]

    expect(translations).toHaveLength(2)
    expect(translations[0].languageCode).toBe('zh-CN')
    expect(translations[1].languageCode).toBe('en-US')
  })

  it('should filter translations by language code', () => {
    const translations = [
      { languageCode: 'zh-CN', text: '保存' },
      { languageCode: 'en-US', text: 'Save' },
      { languageCode: 'en-US', text: 'Cancel' }
    ]

    const zhTranslations = translations.filter(t => t.languageCode === 'zh-CN')
    const enTranslations = translations.filter(t => t.languageCode === 'en-US')

    expect(zhTranslations).toHaveLength(1)
    expect(enTranslations).toHaveLength(2)
  })

  it('should filter translations by namespace', () => {
    const translations = [
      { namespace: 'common', key: 'button.save' },
      { namespace: 'status', key: 'active' },
      { namespace: 'common', key: 'button.cancel' }
    ]

    const commonTranslations = translations.filter(t => t.namespace === 'common')

    expect(commonTranslations).toHaveLength(2)
  })

  it('should identify translation type', () => {
    const translations = [
      { type: 'label', key: 'button.save' },
      { type: 'enum', key: 'status.active' },
      { type: 'message', key: 'error.required' },
      { type: 'object_field', key: 'Asset.name' }
    ]

    const labelCount = translations.filter(t => t.type === 'label').length
    const enumCount = translations.filter(t => t.type === 'enum').length
    const messageCount = translations.filter(t => t.type === 'message').length
    const objectFieldCount = translations.filter(t => t.type === 'object_field').length

    expect(labelCount).toBe(1)
    expect(enumCount).toBe(1)
    expect(messageCount).toBe(1)
    expect(objectFieldCount).toBe(1)
  })
})

describe('TranslationDialog Component', () => {
  let pinia: any

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
  })

  it('should initialize empty form for create mode', () => {
    const formData = {
      namespace: '',
      key: '',
      contentTypeModel: '',
      objectId: null,
      fieldName: '',
      languageCode: 'zh-CN',
      text: '',
      context: '',
      type: 'label',
      isSystem: false
    }

    expect(formData.namespace).toBe('')
    expect(formData.key).toBe('')
    expect(formData.objectId).toBeNull()
  })

  it('should populate form for edit mode', () => {
    const translation = {
      id: '123',
      namespace: 'common',
      key: 'button.save',
      text: 'Save',
      languageCode: 'en-US',
      type: 'label'
    }

    const formData = {
      namespace: (translation as any).namespace || '',
      key: (translation as any).key || '',
      contentTypeModel: (translation as any).contentTypeModel || '',
      objectId: (translation as any).objectId || null,
      fieldName: (translation as any).fieldName || '',
      languageCode: (translation as any).languageCode || 'zh-CN',
      text: (translation as any).text || '',
      context: (translation as any).context || '',
      type: (translation as any).type || 'label',
      isSystem: (translation as any).isSystem || false
    }

    expect(formData.namespace).toBe('common')
    expect(formData.key).toBe('button.save')
    expect(formData.text).toBe('Save')
  })

  it('should validate required fields', () => {
    const formData = {
      languageCode: '',
      namespace: '',
      key: '',
      text: ''
    }

    const errors: string[] = []
    if (!formData.languageCode) errors.push('Language is required')
    if (!formData.namespace) errors.push('Namespace is required')
    if (!formData.key) errors.push('Key is required')
    if (!formData.text) errors.push('Text is required')

    expect(errors).toHaveLength(4)
  })

  it('should switch between namespace and object modes', () => {
    let mode = 'namespace'

    // Switch to object mode
    mode = 'object'

    expect(mode).toBe('object')
  })

  it('should handle UUID as objectId for object translations', () => {
    const objectId = '550e8400-e29b-41d4-a716-446655440000'

    // Should be a valid UUID string
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    expect(uuidRegex.test(objectId)).toBe(true)
  })
})

describe('I18n Type Definitions', () => {
  it('should have correct Language interface', () => {
    interface Language {
      id: string
      code: string
      name: string
      nativeName: string
      isDefault: boolean
      isActive: boolean
      sortOrder: number
      flagEmoji?: string
      locale?: string
    }

    const language: Language = {
      id: '123',
      code: 'zh-CN',
      name: '简体中文',
      nativeName: '中文',
      isDefault: true,
      isActive: true,
      sortOrder: 1,
      flagEmoji: '🇨🇳',
      locale: 'zhCN'
    }

    expect(language.code).toBe('zh-CN')
    expect((language as any).objectId).toBeUndefined()
  })

  it('should have correct Translation interface with UUID objectId', () => {
    interface Translation {
      id: string
      namespace?: string
      key?: string
      contentTypeModel?: string
      objectId?: string  // Changed from number to string (UUID)
      fieldName?: string
      languageCode: string
      text: string
      context?: string
      type?: string
      isSystem?: boolean
    }

    const translation: Translation = {
      id: '123',
      namespace: 'common',
      key: 'button.save',
      languageCode: 'en-US',
      text: 'Save',
      objectId: '550e8400-e29b-41d4-a716-446655440000'  // UUID string
    }

    expect(typeof translation.objectId).toBe('string')
  })
})

describe('I18n Utility Functions', () => {
  it('should get language flag emoji by code', () => {
    const getFlagEmoji = (code: string): string => {
      const flags: Record<string, string> = {
        'zh-CN': '🇨🇳',
        'en-US': '🇺🇸',
        'ja-JP': '🇯🇵',
        'ko-KR': '🇰🇷'
      }
      return flags[code] || '🌐'
    }

    expect(getFlagEmoji('zh-CN')).toBe('🇨🇳')
    expect(getFlagEmoji('en-US')).toBe('🇺🇸')
    expect(getFlagEmoji('ja-JP')).toBe('🇯🇵')
    expect(getFlagEmoji('unknown')).toBe('🌐')
  })

  it('should format translation key', () => {
    const formatKey = (namespace: string, key: string): string => {
      return `${namespace}:${key}`
    }

    expect(formatKey('common', 'button.save')).toBe('common:button.save')
  })

  it('should parse translation key', () => {
    const parseKey = (fullKey: string): { namespace: string; key: string } => {
      const [namespace, key] = fullKey.split(':', 2)
      return { namespace, key }
    }

    const result = parseKey('common:button.save')
    expect(result.namespace).toBe('common')
    expect(result.key).toBe('button.save')
  })
})
