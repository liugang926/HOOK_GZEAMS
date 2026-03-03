import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'
import ElementPlus from 'element-plus'

const listMock = vi.fn()

vi.mock('@/api/permissions', () => ({
  fieldPermissionApi: {
    list: (...args: unknown[]) => listMock(...args)
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

describe('FieldPermissionTab API integration', () => {
  beforeEach(() => {
    listMock.mockReset()
  })

  it('loads field permission rows from backend API response', async () => {
    listMock.mockResolvedValue({
      count: 1,
      results: [
        {
          id: 'fp-1',
          user: 'u-1',
          userDisplay: 'bob',
          contentType: 1,
          contentTypeDisplay: 'asset',
          fieldName: 'asset_name',
          permissionType: 'write',
          permissionTypeDisplay: 'Write',
          description: 'field-from-api'
        }
      ]
    })

    const FieldPermissionTab = (await import('@/views/admin/components/FieldPermissionTab.vue')).default

    const wrapper = mount(FieldPermissionTab, {
      global: {
        plugins: [ElementPlus],
        mocks: {
          $t: (key: string) => key
        },
        stubs: {
          FieldPermissionDialog: defineComponent({
            name: 'FieldPermissionDialog',
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
    expect(text).toContain('bob')
    expect(text).toContain('asset')
    expect(text).toContain('asset_name')
    expect(text).toContain('field-from-api')
  })
})
