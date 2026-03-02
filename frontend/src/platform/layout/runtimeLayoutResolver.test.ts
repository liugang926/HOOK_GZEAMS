import { beforeEach, describe, expect, it, vi } from 'vitest'
import { resolveRuntimeLayout } from './runtimeLayoutResolver'
import { dynamicApi } from '@/api/dynamic'
import { businessObjectApi, pageLayoutApi } from '@/api/system'

vi.mock('@/api/dynamic', () => ({
  dynamicApi: {
    getRuntime: vi.fn()
  }
}))

vi.mock('@/api/system', () => ({
  businessObjectApi: {
    getFieldsWithContext: vi.fn()
  },
  pageLayoutApi: {
    getDefault: vi.fn()
  }
}))

describe('resolveRuntimeLayout', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns readonly runtime payload directly from backend shared model', async () => {
    vi.mocked(dynamicApi.getRuntime).mockResolvedValue({
      context: 'form',
      fields: {
        editableFields: [{ code: 'name', fieldType: 'text' }],
        reverseRelations: [{ code: 'maintenanceRecords', fieldType: 'sub_table' }]
      },
      permissions: {
        view: true,
        add: true,
        change: false,
        delete: false
      },
      isDefault: false,
      layout: {
        status: 'published',
        version: '2.1.0',
        layoutConfig: {
          sections: [
            {
              id: 'basic',
              type: 'section',
              title: 'Basic Information',
              fields: [{ fieldCode: 'name', label: 'Name', span: 12 }]
            }
          ]
        }
      }
    } as any)

    const result = await resolveRuntimeLayout('Asset', 'readonly', { includeRelations: true })

    expect(result.source).toBe('runtime')
    expect(result.runtimeMode).toBe('readonly')
    expect(result.metadataContext).toBe('form')
    expect(result.layoutType).toBe('form')
    expect(result.layoutStatus).toBe('published')
    expect(result.layoutVersion).toBe('2.1.0')
    expect(result.isDefault).toBe(false)
    expect(result.permissions).toEqual({
      view: true,
      add: true,
      change: false,
      delete: false
    })
    expect(result.fields).toHaveLength(2)
    expect(result.layoutConfig?.sections?.length).toBe(1)
    expect(result.layoutConfig?.sections?.[0]?.fields?.[0]?.fieldCode).toBe('name')
    expect(dynamicApi.getRuntime).toHaveBeenCalledTimes(1)
    expect(businessObjectApi.getFieldsWithContext).not.toHaveBeenCalled()
    expect(pageLayoutApi.getDefault).not.toHaveBeenCalled()
  })

  it('returns runtime payload when non-readonly runtime endpoint succeeds', async () => {
    vi.mocked(dynamicApi.getRuntime).mockResolvedValue({
      fields: {
        editableFields: [{ code: 'name', fieldType: 'text' }],
        reverseRelations: [{ code: 'maintenanceRecords', fieldType: 'sub_table' }]
      },
      permissions: {
        view: true,
        add: true,
        change: false,
        delete: false
      },
      isDefault: false,
      layout: {
        status: 'published',
        version: '2.1.0',
        layoutConfig: {
          sections: [
            {
              id: 'basic',
              type: 'section',
              fields: [{ fieldCode: 'name', label: 'Name', span: 12 }]
            }
          ]
        }
      }
    } as any)

    const result = await resolveRuntimeLayout('Asset', 'edit', { includeRelations: true })

    expect(result.source).toBe('runtime')
    expect(result.runtimeMode).toBe('edit')
    expect(result.layoutType).toBe('form')
    expect(result.layoutStatus).toBe('published')
    expect(result.layoutVersion).toBe('2.1.0')
    expect(result.isDefault).toBe(false)
    expect(result.permissions).toEqual({
      view: true,
      add: true,
      change: false,
      delete: false
    })
    expect(result.fields).toHaveLength(2)
    expect(result.layoutConfig?.sections?.length).toBe(1)
    expect(dynamicApi.getRuntime).toHaveBeenCalledTimes(1)
    expect(businessObjectApi.getFieldsWithContext).not.toHaveBeenCalled()
    expect(pageLayoutApi.getDefault).not.toHaveBeenCalled()
  })

  it('falls back to legacy endpoints when runtime fails', async () => {
    vi.mocked(dynamicApi.getRuntime).mockRejectedValue(new Error('runtime failed'))
    vi.mocked(businessObjectApi.getFieldsWithContext).mockResolvedValue({
      editableFields: [{ code: 'assetName', fieldType: 'text' }],
      reverseRelations: []
    } as any)
    vi.mocked(pageLayoutApi.getDefault).mockResolvedValue({
      isDefault: true,
      version: '1.0.0',
      layoutConfig: {
        sections: [{ id: 's1', type: 'section', fields: [{ fieldCode: 'assetName' }] }]
      }
    } as any)

    const result = await resolveRuntimeLayout('Asset', 'detail')

    expect(result.source).toBe('legacy')
    expect(result.runtimeMode).toBe('readonly')
    expect(result.metadataContext).toBe('form')
    expect(result.layoutType).toBe('form')
    expect(result.isDefault).toBe(true)
    expect(result.layoutVersion).toBe('1.0.0')
    expect(result.permissions).toBeNull()
    expect(result.fields).toHaveLength(1)
    expect(result.layoutConfig?.sections?.[0]?.fields?.[0]?.fieldCode).toBe('assetName')
    expect(businessObjectApi.getFieldsWithContext).toHaveBeenCalledWith('Asset', 'form', { includeRelations: true })
    expect(pageLayoutApi.getDefault).toHaveBeenCalledTimes(1)
    expect(pageLayoutApi.getDefault).toHaveBeenCalledWith('Asset', 'form')
  })
})
