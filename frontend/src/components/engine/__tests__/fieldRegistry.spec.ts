import { describe, expect, it } from 'vitest'
import {
  FIELD_COMPONENT_LOADERS,
  buildNormalizedRuntimeField,
  getFieldComponentLoader,
  getSupportedEngineFieldTypes,
  isEngineFieldSupportedInMode,
  normalizeEngineFieldType,
  resolveEngineFieldType
} from '../fieldRegistry'

describe('fieldRegistry', () => {
  it('normalizes legacy aliases to canonical engine types', () => {
    expect(normalizeEngineFieldType('multiselect')).toBe('multi_select')
    expect(normalizeEngineFieldType('subtable')).toBe('sub_table')
    expect(normalizeEngineFieldType('richtext')).toBe('rich_text')
  })

  it('resolves engine type from mixed payload shape', () => {
    expect(resolveEngineFieldType({ fieldType: 'multiSelect' })).toBe('multi_select')
    expect(resolveEngineFieldType({ field_type: 'subtable' })).toBe('sub_table')
    expect(resolveEngineFieldType({ type: 'richtext' })).toBe('rich_text')
  })

  it('returns the same loader for alias and canonical type', () => {
    expect(getFieldComponentLoader('multiselect')).toBe(FIELD_COMPONENT_LOADERS.multi_select)
    expect(getFieldComponentLoader('subtable')).toBe(FIELD_COMPONENT_LOADERS.sub_table)
    expect(getFieldComponentLoader('richtext')).toBe(FIELD_COMPONENT_LOADERS.rich_text)
  })

  it('normalizes runtime field and merges component props with camelCase precedence', () => {
    const result = buildNormalizedRuntimeField({
      field_type: 'subtable',
      component_props: { rows: 2, mode: 'legacy' },
      componentProps: { rows: 6 }
    })

    expect(result.fieldType).toBe('sub_table')
    expect(result.field_type).toBe('sub_table')
    expect(result.componentProps.rows).toBe(6)
    expect(result.componentProps.mode).toBe('legacy')
    expect(result.component_props.rows).toBe(6)
  })

  it('keeps a stable supported type baseline for engine rendering', () => {
    const supported = getSupportedEngineFieldTypes()

    expect(supported.length).toBe(25)
    expect(supported).toEqual(expect.arrayContaining([
      'text', 'number', 'date', 'datetime',
      'select', 'multi_select', 'reference',
      'sub_table', 'file', 'image', 'rich_text'
    ]))
  })

  it('checks render-mode support from capability matrix', () => {
    expect(isEngineFieldSupportedInMode('rich_text', 'search')).toBe(false)
    expect(isEngineFieldSupportedInMode('subtable', 'list')).toBe(false)
    expect(isEngineFieldSupportedInMode('text', 'search')).toBe(true)
  })
})
