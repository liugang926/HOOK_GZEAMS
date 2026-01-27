/**
 * Unit tests for layout validation utilities
 */

import { describe, it, expect } from 'vitest'
import {
  validateLayoutConfig,
  validateAndSanitizeLayoutConfig,
  getDefaultLayoutConfig,
  generateId,
  cloneLayoutConfig,
  isLayoutConfigEmpty
} from './layoutValidation'
import type { LayoutType } from './layoutValidation'

describe('layoutValidation', () => {
  describe('validateLayoutConfig', () => {
    it('should validate a correct form layout', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'section',
            title: 'Basic Info',
            fields: [
              {
                id: 'field-1',
                field_code: 'name',
                label: 'Name',
                span: 12
              }
            ]
          }
        ]
      }

      const result = validateLayoutConfig(config, 'form')
      expect(result.valid).toBe(true)
      expect(result.errors).toHaveLength(0)
    })

    it('should reject form layout without sections', () => {
      const config = {}

      const result = validateLayoutConfig(config, 'form')
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.path === 'sections')).toBe(true)
    })

    it('should reject form layout with empty sections array', () => {
      const config = { sections: [] }

      const result = validateLayoutConfig(config, 'form')
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.message.includes('cannot be empty'))).toBe(true)
    })

    it('should reject section without id', () => {
      const config = {
        sections: [
          {
            type: 'section',
            title: 'Test',
            fields: []
          }
        ]
      }

      const result = validateLayoutConfig(config, 'form')
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.message.includes('id'))).toBe(true)
    })

    it('should reject section without type', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            title: 'Test',
            fields: []
          }
        ]
      }

      const result = validateLayoutConfig(config, 'form')
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.message.includes('type'))).toBe(true)
    })

    it('should reject invalid section type', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'invalid_type',
            fields: []
          }
        ]
      }

      const result = validateLayoutConfig(config, 'form')
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.message.includes('Invalid type'))).toBe(true)
    })

    it('should reject field without required attributes', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'section',
            fields: [
              {
                id: 'field-1',
                field_code: 'test',
                label: 'Test'
                // Missing span
              }
            ]
          }
        ]
      }

      const result = validateLayoutConfig(config, 'form')
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.message.includes('span'))).toBe(true)
    })

    it('should reject invalid span value', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'section',
            fields: [
              {
                id: 'field-1',
                field_code: 'test',
                label: 'Test',
                span: 5 // Invalid span
              }
            ]
          }
        ]
      }

      const result = validateLayoutConfig(config, 'form')
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.message.includes('span'))).toBe(true)
    })

    it('should validate a correct tab section', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'tab',
            tabs: [
              {
                id: 'tab-1',
                title: 'Tab 1',
                fields: [
                  {
                    id: 'field-1',
                    field_code: 'test',
                    label: 'Test',
                    span: 12
                  }
                ]
              }
            ]
          }
        ]
      }

      const result = validateLayoutConfig(config, 'form')
      expect(result.valid).toBe(true)
    })

    it('should reject tab section without tabs', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'tab',
            tabs: []
          }
        ]
      }

      const result = validateLayoutConfig(config, 'form')
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.message.includes('tabs'))).toBe(true)
    })

    it('should validate a correct list layout', () => {
      const config = {
        columns: [
          {
            field_code: 'name',
            label: 'Name',
            width: 200
          }
        ]
      }

      const result = validateLayoutConfig(config, 'list')
      expect(result.valid).toBe(true)
    })

    it('should reject list layout without columns', () => {
      const config = {}

      const result = validateLayoutConfig(config, 'list')
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.path === 'columns')).toBe(true)
    })

    it('should reject list column without required fields', () => {
      const config = {
        columns: [
          {
            field_code: 'test'
            // Missing label
          }
        ]
      }

      const result = validateLayoutConfig(config, 'list')
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.message.includes('label'))).toBe(true)
    })
  })

  describe('validateAndSanitizeLayoutConfig', () => {
    it('should sanitize valid config', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'section',
            title: 'Test',
            fields: []
          }
        ]
      }

      const result = validateAndSanitizeLayoutConfig(config, 'form')
      expect(result.valid).toBe(true)
      expect(result.sanitized).toBeDefined()
      expect(result.sanitized?.sections).toEqual(config.sections)
    })

    it('should add default actions for form layout', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'section',
            fields: []
          }
        ]
      }

      const result = validateAndSanitizeLayoutConfig(config, 'form')
      expect(result.valid).toBe(true)
      expect(result.sanitized?.actions).toEqual([])
    })
  })

  describe('getDefaultLayoutConfig', () => {
    it('should return default form config', () => {
      const config = getDefaultLayoutConfig('form')
      expect(config).toHaveProperty('sections')
      expect(config.sections).toBeInstanceOf(Array)
      expect(config.sections?.length).toBeGreaterThan(0)
      expect(config.sections?.[0]).toHaveProperty('type', 'section')
    })

    it('should return default list config', () => {
      const config = getDefaultLayoutConfig('list')
      expect(config).toHaveProperty('columns')
      expect(config.columns).toBeInstanceOf(Array)
      expect(config).toHaveProperty('page_size', 20)
      expect(config).toHaveProperty('show_pagination', true)
    })

    it('should return default detail config', () => {
      const config = getDefaultLayoutConfig('detail')
      expect(config).toHaveProperty('sections')
      expect(config.sections).toBeInstanceOf(Array)
    })

    it('should return default search config', () => {
      const config = getDefaultLayoutConfig('search')
      expect(config).toHaveProperty('fields')
      expect(config).toHaveProperty('layout', 'horizontal')
    })
  })

  describe('generateId', () => {
    it('should generate unique IDs', () => {
      const id1 = generateId('test')
      const id2 = generateId('test')
      expect(id1).not.toBe(id2)
    })

    it('should include prefix', () => {
      const id = generateId('prefix')
      expect(id.startsWith('prefix-')).toBe(true)
    })
  })

  describe('cloneLayoutConfig', () => {
    it('should deep clone config', () => {
      const original = {
        sections: [
          {
            id: 'section-1',
            type: 'section',
            fields: [{ id: 'field-1', field_code: 'test', label: 'Test', span: 12 }]
          }
        ]
      }

      const clone = cloneLayoutConfig(original)

      // Modify clone
      clone.sections[0].id = 'modified'

      // Original should be unchanged
      expect(original.sections[0].id).toBe('section-1')
    })
  })

  describe('isLayoutConfigEmpty', () => {
    it('should detect empty form layout', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'section',
            fields: []
          }
        ]
      }

      expect(isLayoutConfigEmpty(config, 'form')).toBe(true)
    })

    it('should detect non-empty form layout', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'section',
            fields: [{ id: 'field-1', field_code: 'test', label: 'Test', span: 12 }]
          }
        ]
      }

      expect(isLayoutConfigEmpty(config, 'form')).toBe(false)
    })

    it('should detect empty tab layout', () => {
      const config = {
        sections: [
          {
            id: 'section-1',
            type: 'tab',
            tabs: [
              { id: 'tab-1', title: 'Tab 1', fields: [] }
            ]
          }
        ]
      }

      expect(isLayoutConfigEmpty(config, 'form')).toBe(true)
    })

    it('should detect empty list layout', () => {
      const config = { columns: [] }
      expect(isLayoutConfigEmpty(config, 'list')).toBe(true)
    })

    it('should detect non-empty list layout', () => {
      const config = {
        columns: [{ field_code: 'test', label: 'Test' }]
      }
      expect(isLayoutConfigEmpty(config, 'list')).toBe(false)
    })
  })
})
