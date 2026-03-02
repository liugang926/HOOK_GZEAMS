import { describe, expect, it } from 'vitest'
import { buildSearchFields } from './searchFieldBuilder'

describe('searchFieldBuilder', () => {
  it('builds search fields and maps input control types', () => {
    const result = buildSearchFields([
      { code: 'name', name: 'Name', fieldType: 'text', isSearchable: true },
      { code: 'status', name: 'Status', fieldType: 'select', isSearchable: true, options: [{ label: 'A', value: 'a' }] },
      { code: 'enabled', name: 'Enabled', fieldType: 'boolean', isSearchable: true },
      { code: 'createdAt', name: 'Created At', fieldType: 'datetime', isSearchable: true },
    ] as Record<string, unknown>[])

    expect(result).toHaveLength(4)
    expect(result.find((item) => item.prop === 'name')?.type).toBe('text')
    expect(result.find((item) => item.prop === 'status')?.type).toBe('select')
    expect(result.find((item) => item.prop === 'enabled')?.type).toBe('boolean')
    expect(result.find((item) => item.prop === 'createdAt')?.type).toBe('date')
  })

  it('filters out fields unsupported in search mode by capability matrix', () => {
    const result = buildSearchFields([
      { code: 'photo', name: 'Photo', fieldType: 'image', isSearchable: true },
      { code: 'tableRows', name: 'Rows', fieldType: 'subtable', isSearchable: true },
      { code: 'desc', name: 'Description', fieldType: 'rich_text', isSearchable: true },
      { code: 'name', name: 'Name', fieldType: 'text', isSearchable: true },
    ] as Record<string, unknown>[])

    expect(result.map((item) => item.prop)).toEqual(['name'])
  })

  it('supports legacy snake/camel searchability flags and multiselect', () => {
    const result = buildSearchFields([
      { code: 'tags', name: 'Tags', field_type: 'multiSelect', is_searchable: true, options: [] },
    ] as Record<string, unknown>[])

    expect(result).toHaveLength(1)
    expect(result[0].type).toBe('select')
    expect(result[0].multiple).toBe(true)
  })
})
