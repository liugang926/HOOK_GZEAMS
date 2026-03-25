import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useDynamicForm } from '../useDynamicForm'

vi.mock('@/platform/layout/runtimeLayoutResolver', () => ({
  resolveRuntimeLayout: vi.fn()
}))

import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'

describe('useDynamicForm initialization strategy', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('applies defaults only in create mode and keeps sort order stable', async () => {
    vi.mocked(resolveRuntimeLayout).mockResolvedValue({
      fields: [
        { code: 'assetCode', name: 'Asset Code', fieldType: 'text', sortOrder: 2, defaultValue: 'ASSET-NEW-001' },
        { code: 'assetName', name: 'Asset Name', fieldType: 'text', sortOrder: 1 }
      ],
      layoutConfig: null
    } as any)

    const form = useDynamicForm('Asset', 'form', null, null, null)
    await form.loadMetadata()

    expect(form.fieldDefinitions.value.map((item) => item.code)).toEqual(['assetName', 'assetCode'])
    expect(form.formData.value.assetCode).toBe('ASSET-NEW-001')
  })

  it('does not inject create defaults in edit mode', async () => {
    vi.mocked(resolveRuntimeLayout).mockResolvedValue({
      fields: [
        { code: 'assetCode', name: 'Asset Code', fieldType: 'text', sortOrder: 1, defaultValue: 'ASSET-NEW-001' }
      ],
      layoutConfig: null
    } as any)

    const form = useDynamicForm('Asset', 'form', null, null, 'asset-1')
    await form.loadMetadata()

    expect(Object.prototype.hasOwnProperty.call(form.formData.value, 'assetCode')).toBe(false)
  })

  it('injects runtime line items into form layout and initializes sub tables to empty arrays', async () => {
    vi.mocked(resolveRuntimeLayout).mockResolvedValue({
      fields: [
        { code: 'pickupReason', name: 'Pickup Reason', fieldType: 'text', sortOrder: 1 },
        {
          code: 'items',
          name: 'Items',
          fieldType: 'sub_table',
          sortOrder: 2,
          relatedFields: [
            { code: 'asset', name: 'Asset', fieldType: 'asset' },
            { code: 'quantity', name: 'Quantity', fieldType: 'number' }
          ]
        }
      ],
      layoutConfig: {
        sections: [
          {
            id: 'main',
            type: 'section',
            fields: [{ fieldCode: 'pickupReason', label: 'Pickup Reason' }]
          }
        ]
      }
    } as any)

    const form = useDynamicForm('AssetPickup', 'form', null, null, null)
    await form.loadMetadata()

    const firstSection = form.runtimeLayout.value.sections?.[0]
    const fieldCodes = (firstSection?.fields || []).map((field: any) => field.code)

    expect(fieldCodes).toContain('items')
    expect(form.formData.value.items).toEqual([])
  })
})
