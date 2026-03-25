import { describe, expect, it } from 'vitest'
import {
  getCoreFieldTypes,
  getFieldCapability,
  isFieldSupportedInMode,
} from './fieldCapabilityMatrix'
import { FIELD_COMPONENT_LOADERS } from '@/components/engine/fieldRegistry'

describe('fieldCapabilityMatrix', () => {
  it('provides a stable core 25 field-type baseline', () => {
    const types = getCoreFieldTypes()
    expect(types).toHaveLength(25)
    expect(types).toEqual(expect.arrayContaining([
      'text',
      'textarea',
      'number',
      'currency',
      'date',
      'select',
      'reference',
      'sub_table',
      'formula',
      'file',
      'image',
      'rich_text',
    ]))
  })

  it('keeps runtime-only field types supported without promoting them into the core baseline', () => {
    const types = getCoreFieldTypes()
    expect(types).not.toContain('related_object')
    expect(types).not.toContain('workflow_progress')

    expect(getFieldCapability('related_object').componentType).toBe('related_object')
    expect(getFieldCapability('workflow_progress').componentType).toBe('workflow_progress')
  })

  it('normalizes aliases and resolves component strategy', () => {
    const multiSelect = getFieldCapability('multiSelect')
    const subtable = getFieldCapability('subtable')
    expect(multiSelect.type).toBe('multi_select')
    expect(multiSelect.componentType).toBe('multi_select')
    expect(subtable.type).toBe('sub_table')
    expect(subtable.componentType).toBe('sub_table')
  })

  it('returns mode capability flags for runtime checks', () => {
    expect(isFieldSupportedInMode('rich_text', 'search')).toBe(false)
    expect(isFieldSupportedInMode('file', 'search')).toBe(false)
    expect(isFieldSupportedInMode('text', 'search')).toBe(true)
    expect(isFieldSupportedInMode('formula', 'readonly')).toBe(true)
  })

  it('keeps 25-core-type mode matrix stable and mappable to renderers', () => {
    const expectedModes: Record<string, { edit: boolean; readonly: boolean; list: boolean; search: boolean }> = {
      text: { edit: true, readonly: true, list: true, search: true },
      textarea: { edit: true, readonly: true, list: false, search: true },
      number: { edit: true, readonly: true, list: true, search: true },
      currency: { edit: true, readonly: true, list: true, search: true },
      percent: { edit: true, readonly: true, list: true, search: true },
      date: { edit: true, readonly: true, list: true, search: true },
      datetime: { edit: true, readonly: true, list: true, search: true },
      time: { edit: true, readonly: true, list: true, search: true },
      select: { edit: true, readonly: true, list: true, search: true },
      multi_select: { edit: true, readonly: true, list: true, search: true },
      radio: { edit: true, readonly: true, list: true, search: true },
      checkbox: { edit: true, readonly: true, list: true, search: true },
      boolean: { edit: true, readonly: true, list: true, search: true },
      user: { edit: true, readonly: true, list: true, search: true },
      department: { edit: true, readonly: true, list: true, search: true },
      reference: { edit: true, readonly: true, list: true, search: true },
      asset: { edit: true, readonly: true, list: true, search: true },
      location: { edit: true, readonly: true, list: true, search: true },
      file: { edit: true, readonly: true, list: true, search: false },
      image: { edit: true, readonly: true, list: true, search: false },
      rich_text: { edit: true, readonly: true, list: false, search: false },
      qr_code: { edit: true, readonly: true, list: true, search: false },
      barcode: { edit: true, readonly: true, list: true, search: false },
      sub_table: { edit: true, readonly: true, list: false, search: false },
      formula: { edit: true, readonly: true, list: true, search: false },
    }

    const coreTypes = getCoreFieldTypes()
    expect(coreTypes).toHaveLength(25)

    for (const type of coreTypes) {
      const expected = expectedModes[type]
      expect(expected).toBeDefined()

      expect(isFieldSupportedInMode(type, 'edit')).toBe(expected.edit)
      expect(isFieldSupportedInMode(type, 'readonly')).toBe(expected.readonly)
      expect(isFieldSupportedInMode(type, 'list')).toBe(expected.list)
      expect(isFieldSupportedInMode(type, 'search')).toBe(expected.search)

      const capability = getFieldCapability(type)
      expect(typeof FIELD_COMPONENT_LOADERS[capability.componentType]).toBe('function')
    }
  })
})
