import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ElementPlus from 'element-plus'

const createMock = vi.fn()
const updateMock = vi.fn()
const fetchPermissionUserOptionsMock = vi.fn()
const fetchPermissionObjectOptionsMock = vi.fn()

vi.mock('@/api/permissions', () => ({
  dataPermissionApi: {
    create: (...args: unknown[]) => createMock(...args),
    update: (...args: unknown[]) => updateMock(...args)
  }
}))

vi.mock('@/views/admin/components/permissionOptions', () => ({
  fetchPermissionUserOptions: (...args: unknown[]) => fetchPermissionUserOptionsMock(...args),
  fetchPermissionObjectOptions: (...args: unknown[]) => fetchPermissionObjectOptionsMock(...args)
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

type DataPermissionDialogVm = {
  formData: {
    roleName: string
    businessObjectName: string
    permissionType: 'all' | 'department' | 'department_and_sub' | 'self' | 'custom'
    scopeExpression: string
    description: string
  }
  formRef: {
    validate: (cb: (valid: boolean) => void | Promise<void>) => Promise<void>
    clearValidate?: () => void
  }
  handleSubmit: () => Promise<void>
}

const forceFormValid = (vm: DataPermissionDialogVm) => {
  vm.formRef = {
    validate: async (cb) => {
      await cb(true)
    },
    clearValidate: () => {}
  }
}

describe('DataPermissionDialog submit payload', () => {
  beforeEach(() => {
    createMock.mockReset()
    updateMock.mockReset()
    fetchPermissionUserOptionsMock.mockReset()
    fetchPermissionObjectOptionsMock.mockReset()

    fetchPermissionUserOptionsMock.mockResolvedValue([{ label: 'alice', value: 'alice' }])
    fetchPermissionObjectOptionsMock.mockResolvedValue([{ label: 'Asset', value: 'assets.asset' }])
  })

  it('submits create payload with app.model mapping', async () => {
    const DataPermissionDialog = (await import('@/views/admin/components/DataPermissionDialog.vue')).default

    const wrapper = mount(DataPermissionDialog, {
      props: {
        visible: false
      },
      global: {
        plugins: [ElementPlus],
        mocks: {
          $t: (key: string) => key
        },
        stubs: {
          teleport: true
        }
      }
    })

    await wrapper.setProps({ visible: true })
    await flushPromises()
    await nextTick()

    const vm = wrapper.vm as unknown as DataPermissionDialogVm
    forceFormValid(vm)
    vm.formData.roleName = 'alice'
    vm.formData.businessObjectName = 'assets.asset'
    vm.formData.permissionType = 'department'
    vm.formData.description = 'dept scope'

    await nextTick()
    await vm.handleSubmit()
    await flushPromises()

    expect(createMock).toHaveBeenCalledTimes(1)
    expect(createMock).toHaveBeenCalledWith({
      userUsername: 'alice',
      contentTypeAppLabel: 'assets',
      contentTypeModel: 'asset',
      scopeType: 'self_dept',
      scopeValue: {},
      departmentField: 'department',
      userField: 'created_by',
      description: 'dept scope'
    })
    expect(updateMock).not.toHaveBeenCalled()
  })

  it('preserves legacy specified scope in edit mode when expression is empty', async () => {
    const DataPermissionDialog = (await import('@/views/admin/components/DataPermissionDialog.vue')).default
    const legacyScopeValue = { ids: [1, 2, 3] }

    const wrapper = mount(DataPermissionDialog, {
      props: {
        visible: false,
        data: {
          id: 'dp-1',
          roleName: 'alice',
          businessObjectName: 'assets.asset',
          permissionType: 'custom',
          scopeType: 'specified',
          scopeValue: legacyScopeValue,
          departmentField: 'department',
          userField: 'created_by',
          description: 'legacy rule'
        }
      },
      global: {
        plugins: [ElementPlus],
        mocks: {
          $t: (key: string) => key
        },
        stubs: {
          teleport: true
        }
      }
    })

    await wrapper.setProps({ visible: true })
    await flushPromises()
    await nextTick()

    const vm = wrapper.vm as unknown as DataPermissionDialogVm
    forceFormValid(vm)
    vm.formData.permissionType = 'custom'
    vm.formData.scopeExpression = ''

    await nextTick()
    await vm.handleSubmit()
    await flushPromises()

    expect(updateMock).toHaveBeenCalledTimes(1)
    expect(updateMock).toHaveBeenCalledWith('dp-1', {
      scopeType: 'specified',
      scopeValue: legacyScopeValue,
      departmentField: 'department',
      userField: 'created_by',
      description: 'legacy rule'
    })
    expect(createMock).not.toHaveBeenCalled()
  })
})
