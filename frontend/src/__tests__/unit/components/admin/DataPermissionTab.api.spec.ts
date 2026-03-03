import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'
import ElementPlus from 'element-plus'

const listMock = vi.fn()
const deleteMock = vi.fn()

vi.mock('@/api/permissions', () => ({
  dataPermissionApi: {
    list: (...args: unknown[]) => listMock(...args),
    delete: (...args: unknown[]) => deleteMock(...args)
  }
}))

vi.mock('@/views/admin/components/permissionOptions', () => ({
  fetchPermissionUserOptions: vi.fn().mockResolvedValue([]),
  fetchPermissionObjectOptions: vi.fn().mockResolvedValue([])
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

describe('DataPermissionTab API integration', () => {
  beforeEach(() => {
    listMock.mockReset()
    deleteMock.mockReset()
  })

  it('loads table rows from backend API response', async () => {
    listMock.mockResolvedValue({
      count: 1,
      results: [
        {
          id: 'perm-1',
          user: 'u-1',
          userDisplay: 'alice',
          contentType: 1,
          contentTypeDisplay: 'asset',
          scopeType: 'all',
          scopeTypeDisplay: 'All Data',
          scopeValue: {},
          departmentField: 'department',
          userField: 'created_by',
          description: 'from-api'
        }
      ]
    })

    const DataPermissionTab = (await import('@/views/admin/components/DataPermissionTab.vue')).default

    const wrapper = mount(DataPermissionTab, {
      global: {
        plugins: [ElementPlus],
        mocks: {
          $t: (key: string) => key
        },
        stubs: {
          DataPermissionDialog: defineComponent({
            name: 'DataPermissionDialog',
            template: '<div />'
          })
        }
      }
    })

    await flushPromises()
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(listMock).toHaveBeenCalledTimes(1)
    expect(listMock).toHaveBeenCalledWith(
      expect.objectContaining({
        page: 1,
        page_size: 20
      })
    )

    const text = wrapper.text()
    expect(text).toContain('alice')
    expect(text).toContain('asset')
    expect(text).toContain('from-api')
  })
})
