import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useLayoutFields, clearAllLayoutFieldsCache } from '../useLayoutFields'
import { businessObjectApi } from '@/api/system'

vi.mock('@/api/system', () => ({
  businessObjectApi: {
    getFieldsWithContext: vi.fn()
  }
}))

describe('useLayoutFields', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    clearAllLayoutFieldsCache()
  })

  it('normalizes field types from mixed API payload shapes', async () => {
    vi.mocked(businessObjectApi.getFieldsWithContext).mockResolvedValue({
      data: {
        data: {
          editableFields: [
            { code: 'title', name: 'Title', fieldType: 'text' },
            { code: 'tags', name: 'Tags', field_type: 'multiSelect' },
            { code: 'content', name: 'Content', type: 'richtext' },
            { code: 'items', name: 'Items', fieldType: 'subtable' },
            { code: 'owner', name: 'Owner', fieldType: 'user' }
          ]
        }
      }
    } as any)

    const { fetchFields, availableFields } = useLayoutFields('Asset')
    await fetchFields()

    const typeByCode = Object.fromEntries(availableFields.value.map((f) => [f.code, f.fieldType]))
    expect(typeByCode.title).toBe('text')
    expect(typeByCode.tags).toBe('multi_select')
    expect(typeByCode.content).toBe('rich_text')
    expect(typeByCode.items).toBe('sub_table')
    expect(typeByCode.owner).toBe('user')
  })

  it('groups canonical field types for layout palette', async () => {
    vi.mocked(businessObjectApi.getFieldsWithContext).mockResolvedValue({
      data: {
        data: {
          editableFields: [
            { code: 'summary', name: 'Summary', fieldType: 'textarea' },
            { code: 'enabled', name: 'Enabled', fieldType: 'switch' },
            { code: 'assignee', name: 'Assignee', fieldType: 'user' },
            { code: 'photo', name: 'Photo', fieldType: 'image' }
          ]
        }
      }
    } as any)

    const { fetchFields, fieldGroups } = useLayoutFields('Asset')
    await fetchFields()

    const groupMap = Object.fromEntries(fieldGroups.value.map((g) => [g.type, g.fields.map((f) => f.code)]))
    expect(groupMap.text).toContain('summary')
    expect(groupMap.selection).toContain('enabled')
    expect(groupMap.reference).toContain('assignee')
    expect(groupMap.media).toContain('photo')
  })

  it('uses cache on repeated fetch for the same object code', async () => {
    vi.mocked(businessObjectApi.getFieldsWithContext).mockResolvedValue({
      data: {
        data: {
          editableFields: [{ code: 'name', name: 'Name', fieldType: 'text' }]
        }
      }
    } as any)

    const { fetchFields } = useLayoutFields('Asset')
    await fetchFields()
    await fetchFields()

    expect(businessObjectApi.getFieldsWithContext).toHaveBeenCalledTimes(1)
  })
})
