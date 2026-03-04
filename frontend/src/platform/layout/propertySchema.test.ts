import { describe, expect, it } from 'vitest'
import {
  getFieldPropertyKeys,
  getFieldPropertySchema,
  getSectionPropertyKeys,
} from './propertySchema'

describe('propertySchema contract', () => {
  it('keeps shared field properties and type-specific additions', () => {
    const textKeys = getFieldPropertyKeys('text')
    expect(textKeys).toEqual(
      expect.arrayContaining(['fieldType', 'label', 'placeholder', 'span', 'minHeight', 'required', 'readonly', 'visible', 'regex_pattern'])
    )
  })

  it('normalizes legacy aliases through fieldType normalization', () => {
    expect(getFieldPropertyKeys('multiselect')).toContain('options')
    expect(getFieldPropertyKeys('richtext')).toContain('toolbar')
  })

  it('avoids duplicate field property keys', () => {
    const keys = getFieldPropertySchema('currency').map((item) => item.key)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('filters section properties by section type', () => {
    expect(getSectionPropertyKeys('section')).toContain('border')
    expect(getSectionPropertyKeys('tab')).not.toContain('border')
  })
})
