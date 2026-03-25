import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ElementPlus from 'element-plus'

const updateMock = vi.fn()

vi.mock('@/api/permissions', () => ({
  fieldPermissionApi: {
    update: (...args: unknown[]) => updateMock(...args)
  }
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

type FieldPermissionDialogVm = {
  formData: {
    isVisible: boolean
  }
  handleSubmit: () => Promise<void>
}

describe('FieldPermissionDialog submit payload', () => {
  beforeEach(() => {
    updateMock.mockReset()
  })

  it('keeps masked permission payload when masked state is unchanged', async () => {
    const FieldPermissionDialog = (await import('@/views/admin/components/FieldPermissionDialog.vue')).default

    const wrapper = mount(FieldPermissionDialog, {
      props: {
        visible: false,
        data: {
          id: 'fp-1',
          roleName: 'alice',
          businessObjectName: 'assets.asset',
          fieldName: 'mobile',
          permissionType: 'masked',
          maskRule: 'mobile',
          customMaskPattern: '***',
          description: 'masked field'
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

    const vm = wrapper.vm as unknown as FieldPermissionDialogVm
    await vm.handleSubmit()
    await flushPromises()

    expect(updateMock).toHaveBeenCalledTimes(1)
    expect(updateMock).toHaveBeenCalledWith('fp-1', {
      permissionType: 'masked',
      maskRule: 'mobile',
      customMaskPattern: '***',
      description: 'masked field'
    })
  })

  it('submits hidden permission and clears mask payload when field becomes hidden', async () => {
    const FieldPermissionDialog = (await import('@/views/admin/components/FieldPermissionDialog.vue')).default

    const wrapper = mount(FieldPermissionDialog, {
      props: {
        visible: false,
        data: {
          id: 'fp-2',
          roleName: 'alice',
          businessObjectName: 'assets.asset',
          fieldName: 'serial_no',
          permissionType: 'write'
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

    const vm = wrapper.vm as unknown as FieldPermissionDialogVm
    vm.formData.isVisible = false

    await nextTick()
    await vm.handleSubmit()
    await flushPromises()

    expect(updateMock).toHaveBeenCalledTimes(1)
    expect(updateMock).toHaveBeenCalledWith('fp-2', {
      permissionType: 'hidden',
      maskRule: null,
      customMaskPattern: '',
      description: ''
    })
  })
})
