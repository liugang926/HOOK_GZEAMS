import { describe, it, expect, vi, beforeEach } from 'vitest'

const userListMock = vi.fn()
const objectListMock = vi.fn()

vi.mock('@/api/users', () => ({
  userApi: {
    list: (...args: unknown[]) => userListMock(...args)
  }
}))

vi.mock('@/api/system', () => ({
  businessObjectApi: {
    list: (...args: unknown[]) => objectListMock(...args)
  }
}))

describe('permissionOptions', () => {
  beforeEach(() => {
    userListMock.mockReset()
    objectListMock.mockReset()
  })

  it('maps users to selector options', async () => {
    userListMock.mockResolvedValue({
      count: 1,
      results: [
        {
          id: 'u1',
          username: 'alice',
          fullName: 'Alice Wang',
          isActive: true
        }
      ]
    })

    const { fetchPermissionUserOptions } = await import('@/views/admin/components/permissionOptions')
    const options = await fetchPermissionUserOptions('ali')

    expect(userListMock).toHaveBeenCalledWith(
      expect.objectContaining({
        page: 1,
        pageSize: 200,
        search: 'ali'
      })
    )
    expect(options).toEqual([
      {
        label: 'Alice Wang (alice)',
        value: 'alice'
      }
    ])
  })

  it('maps business object registry payload to object options', async () => {
    objectListMock.mockResolvedValue({
      hardcoded: [
        {
          id: 'bo-1',
          code: 'Asset',
          name: 'Asset',
          djangoModelPath: 'apps.assets.models.asset.Asset'
        }
      ],
      custom: [
        {
          id: 'bo-2',
          code: 'CustomThing',
          name: 'Custom Thing',
          tableName: 'objects_customthing'
        }
      ]
    })

    const { fetchPermissionObjectOptions } = await import('@/views/admin/components/permissionOptions')
    const options = await fetchPermissionObjectOptions()

    expect(objectListMock).toHaveBeenCalledWith(
      expect.objectContaining({
        page_size: 500,
        is_active: true
      })
    )
    expect(options).toEqual([
      {
        label: 'Asset (Asset)',
        value: 'assets.asset',
        appLabel: 'assets',
        model: 'asset'
      },
      {
        label: 'Custom Thing (CustomThing)',
        value: 'objects.customthing',
        appLabel: 'objects',
        model: 'customthing'
      }
    ])
  })
})
