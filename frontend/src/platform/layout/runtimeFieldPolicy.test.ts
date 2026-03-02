import { describe, expect, it } from 'vitest'
import { isCreateRuntimeContext, sortFieldsByRuntimeOrder } from './runtimeFieldPolicy'

describe('runtimeFieldPolicy', () => {
  it('sorts by explicit sort order and then code', () => {
    const sorted = sortFieldsByRuntimeOrder([
      { code: 'z_field', sortOrder: 2 },
      { code: 'a_field', sortOrder: 1 },
      { code: 'm_field', sortOrder: 2 }
    ])

    expect(sorted.map((item) => item.code)).toEqual(['a_field', 'm_field', 'z_field'])
  })

  it('supports snake_case sort key fallback', () => {
    const sorted = sortFieldsByRuntimeOrder([
      { code: 'field_a' },
      { code: 'field_b', sort_order: 0 }
    ])
    expect(sorted.map((item) => item.code)).toEqual(['field_b', 'field_a'])
  })

  it('detects create context from instance id', () => {
    expect(isCreateRuntimeContext(null)).toBe(true)
    expect(isCreateRuntimeContext(undefined)).toBe(true)
    expect(isCreateRuntimeContext('')).toBe(true)
    expect(isCreateRuntimeContext('asset-1')).toBe(false)
  })
})
