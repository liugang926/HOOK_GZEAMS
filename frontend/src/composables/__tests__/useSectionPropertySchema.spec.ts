import { describe, expect, it } from 'vitest'
import { getSectionPropertyKeys, getSectionPropertySchema } from '../useSectionPropertySchema'

describe('useSectionPropertySchema', () => {
  it('returns common section properties for default section type', () => {
    const keys = getSectionPropertyKeys('section')
    expect(keys).toEqual(expect.arrayContaining(['title', 'columns', 'border', 'collapsible', 'collapsed']))
  })

  it('filters type-specific properties by section type', () => {
    const sectionSchema = getSectionPropertySchema('section')
    const tabSchema = getSectionPropertySchema('tab')

    expect(sectionSchema.some((item) => item.key === 'border')).toBe(true)
    expect(tabSchema.some((item) => item.key === 'border')).toBe(false)
  })
})

