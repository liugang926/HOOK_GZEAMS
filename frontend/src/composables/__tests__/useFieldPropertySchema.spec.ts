import { describe, expect, it } from 'vitest'
import { getFieldPropertyKeys, getFieldPropertySchema } from '../useFieldPropertySchema'

describe('useFieldPropertySchema', () => {
  it('returns shared basic/display properties for all field types', () => {
    const keys = getFieldPropertyKeys('text')
    expect(keys).toEqual(expect.arrayContaining([
      'fieldType', 'label', 'placeholder', 'defaultValue', 'helpText',
      'span', 'required', 'readonly', 'visible'
    ]))
  })

  it('includes type-specific validation properties for numeric fields', () => {
    const keys = getFieldPropertyKeys('currency')
    expect(keys).toEqual(expect.arrayContaining(['min_value', 'max_value', 'precision']))
  })

  it('normalizes legacy aliases before resolving schema', () => {
    expect(getFieldPropertyKeys('multiselect')).toContain('options')
    expect(getFieldPropertyKeys('richtext')).toContain('toolbar')
    expect(getFieldPropertyKeys('subtable')).toContain('relatedFields')
    expect(getFieldPropertyKeys('subtable')).toContain('showShortcutHelp')
    expect(getFieldPropertyKeys('subtable')).toContain('defaultShortcutHelpPinned')
  })

  it('includes reference lookup compact key configuration', () => {
    const keys = getFieldPropertyKeys('reference')
    expect(keys).toContain('lookupCompactKeys')
  })

  it('avoids duplicate property keys', () => {
    const schema = getFieldPropertySchema('text')
    const keys = schema.map((item) => item.key)
    const uniqueSize = new Set(keys).size
    expect(uniqueSize).toBe(keys.length)
  })
})
