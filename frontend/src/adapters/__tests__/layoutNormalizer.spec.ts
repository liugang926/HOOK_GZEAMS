import { describe, expect, it } from 'vitest'
import { normalizeLayoutConfig } from '@/adapters/layoutNormalizer'

describe('layoutNormalizer', () => {
  it('should generate field id when fieldCode exists but id is missing', () => {
    const normalized = normalizeLayoutConfig({
      sections: [
        {
          id: 'section-1',
          type: 'section',
          fields: [
            {
              fieldCode: 'assetName',
              label: 'Asset Name',
              fieldType: 'text'
            }
          ]
        }
      ]
    })

    const field = normalized.sections?.[0]?.fields?.[0] as { id?: string; fieldCode?: string } | undefined
    expect(field?.fieldCode).toBe('assetName')
    expect(typeof field?.id).toBe('string')
    expect((field?.id || '').length).toBeGreaterThan(0)
  })
})
