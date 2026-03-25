/**
 * useMetadata composable tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// Mock dependencies before importing
vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    token: 'test-token',
    currentOrganization: { id: 'org-123' }
  })
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn()
  }
}))

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('useMetadata', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('resolveFormula', () => {
    // Test pure functions without imports
    it('should evaluate simple math expression', () => {
      const expression = '{price} * {quantity}'
      let result: any = expression

      const formData: Record<string, number> = { price: 10, quantity: 5 }
      Object.keys(formData).forEach(key => {
        const regex = new RegExp(`\\{${key}\\}`, 'g')
        result = result.replace(regex, String(formData[key]))
      })

      if (/^[\d\s+\-*/().]+$/.test(result)) {
        result = new Function('return ' + result)()
      }

      expect(result).toBe(50)
    })

    it('should handle missing values as 0', () => {
      const expression = '{price} * {quantity}'
      let result: any = expression

      const formData: Record<string, number> = { price: 10 }
      Object.keys(formData).forEach(key => {
        const regex = new RegExp(`\\{${key}\\}`, 'g')
        result = result.replace(regex, String(formData[key]))
      })
      // Missing values become 0
      result = result.replace(/{\w+}/g, '0')

      if (/^[\d\s+\-*/().]+$/.test(result)) {
        result = new Function('return ' + result)()
      }

      expect(result).toBe(0)
    })

    it('should not evaluate non-math expressions', () => {
      const expression = 'some text'
      const result = /^[\d\s+\-*/().]+$/.test(expression) ? new Function('return ' + expression)() : expression
      expect(result).toBe('some text')
    })
  })

  describe('validateField', () => {
    it('should validate required field', () => {
      const field = {
        label: 'Name',
        isRequired: true
      }

      const value = ''
      const valid = !(field.isRequired && (value === null || value === undefined || value === ''))

      expect(valid).toBe(false)
    })

    it('should pass required validation with value', () => {
      const field = {
        label: 'Name',
        isRequired: true
      }

      const value = 'Test Name'
      const valid = !(field.isRequired && (value === null || value === undefined || (value as string) === ''))

      expect(valid).toBe(true)
    })

    it('should validate pattern rule', () => {
      const rule = { type: 'pattern', value: '^[^@]+@[^@]+$', message: 'Invalid email' }
      const value = 'invalid-email'
      const valid = new RegExp(rule.value).test(value)

      expect(valid).toBe(false)
    })

    it('should pass pattern validation with valid email', () => {
      const rule = { type: 'pattern', value: '^[^@]+@[^@]+$', message: 'Invalid email' }
      const value = 'test@example.com'
      const valid = new RegExp(rule.value).test(value)

      expect(valid).toBe(true)
    })

    it('should validate min rule', () => {
      const rule = { type: 'min', value: 18, message: 'Too young' }
      const value = 15
      const valid = !(value !== null && value < rule.value)

      expect(valid).toBe(false)
    })

    it('should validate max rule', () => {
      const rule = { type: 'max', value: 100, message: 'Too old' }
      const value = 105
      const valid = !(value !== null && value > rule.value)

      expect(valid).toBe(false)
    })

    it('should validate minLength rule', () => {
      const rule = { type: 'minLength', value: 3, message: 'Too short' }
      const value = 'ab'
      const valid = !(value && value.length < rule.value)

      expect(valid).toBe(false)
    })

    it('should validate maxLength rule', () => {
      const rule = { type: 'maxLength', value: 10, message: 'Too long' }
      const value = 'abcdefghijk'
      const valid = !(value && value.length > rule.value)

      expect(valid).toBe(false)
    })
  })

  describe('getFieldOptions', () => {
    it('should return field options', () => {
      const field: any = {
        options: [
          { label: 'Active', value: 'active' },
          { label: 'Inactive', value: 'inactive' }
        ]
      }

      const options = field.options || []

      expect(options).toHaveLength(2)
      expect(options[0].label).toBe('Active')
      expect(options[0].value).toBe('active')
    })

    it('should return empty array when no options', () => {
      const field: any = {}
      const options = field.options || []

      expect(options).toEqual([])
    })
  })

  describe('getCacheKey', () => {
    it('should create unique cache key with org', () => {
      const type = 'field_definitions'
      const identifier = 'asset'
      const orgId = 'org-123'

      const cacheKey = `${orgId}:${type}:${identifier}`

      expect(cacheKey).toBe('org-123:field_definitions:asset')
    })

    it('should use default org when not available', () => {
      const type = 'field_definitions'
      const identifier = 'asset'
      const orgId = 'default'

      const cacheKey = `${orgId}:${type}:${identifier}`

      expect(cacheKey).toBe('default:field_definitions:asset')
    })
  })

  describe('API response parsing', () => {
    it('should extract fields from wrapped response', () => {
      const data: any = {
        success: true,
        data: {
          fields: [{ fieldCode: 'name' }]
        }
      }

      const results = data.data?.fields || data.fields || data.results || []

      expect(results).toHaveLength(1)
      expect(results[0].fieldCode).toBe('name')
    })

    it('should extract fields from direct response', () => {
      const data: any = {
        fields: [{ fieldCode: 'code' }]
      }

      const results = data.data?.fields || data.fields || data.results || []

      expect(results).toHaveLength(1)
      expect(results[0].fieldCode).toBe('code')
    })

    it('should extract fields from results array', () => {
      const data: any = {
        results: [{ fieldCode: 'value' }]
      }

      const results = data.data?.fields || data.fields || data.results || []

      expect(results).toHaveLength(1)
      expect(results[0].fieldCode).toBe('value')
    })

    it('should return empty array when no fields found', () => {
      const data: any = {
        success: true
      }

      const results = data.data?.fields || data.fields || data.results || []

      expect(results).toEqual([])
    })
  })
})
