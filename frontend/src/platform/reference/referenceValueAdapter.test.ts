import { describe, expect, it } from 'vitest'
import {
  buildReferenceValueMap,
  extractEmbeddedReferenceOptions,
  mergeReferenceOptionsByIds
} from '@/platform/reference/referenceValueAdapter'

describe('referenceValueAdapter', () => {
  it('extracts embedded reference objects from single and array values', () => {
    expect(
      extractEmbeddedReferenceOptions({
        id: 'u-1',
        username: 'alice'
      })
    ).toEqual([{ id: 'u-1', username: 'alice' }])

    expect(
      extractEmbeddedReferenceOptions([
        { id: 'u-1', username: 'alice' },
        'u-2',
        { pk: 'u-3', username: 'bob' }
      ])
    ).toEqual([
      { id: 'u-1', username: 'alice' },
      { id: 'u-3', pk: 'u-3', username: 'bob' }
    ])
  })

  it('builds a stable value map and merges embedded with resolved records by id order', () => {
    const embedded = buildReferenceValueMap([
      { id: 'u-1', username: 'alice' },
      { id: 'u-2', username: 'bob' }
    ])

    const merged = mergeReferenceOptionsByIds(
      ['u-2', 'u-1', 'u-3'],
      embedded,
      {
        'u-3': { id: 'u-3', username: 'charlie' }
      }
    )

    expect(merged).toEqual([
      { id: 'u-2', username: 'bob' },
      { id: 'u-1', username: 'alice' },
      { id: 'u-3', username: 'charlie' }
    ])
  })
})
