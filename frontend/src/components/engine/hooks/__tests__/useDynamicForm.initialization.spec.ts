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
})
