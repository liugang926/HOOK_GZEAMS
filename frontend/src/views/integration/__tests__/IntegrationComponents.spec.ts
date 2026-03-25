/* eslint-disable vue/one-component-per-file */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { defineComponent, h, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'

import IntegrationConfigFilterBar from '@/views/integration/components/IntegrationConfigFilterBar.vue'
import IntegrationConfigFormDialog from '@/views/integration/components/IntegrationConfigFormDialog.vue'
import IntegrationLogsDrawer from '@/views/integration/components/IntegrationLogsDrawer.vue'
import { createDefaultIntegrationFormData } from '@/views/integration/integrationConfig.constants'

const createTestI18n = () =>
  createI18n({
    legacy: false,
    locale: 'en',
    missingWarn: false,
    fallbackWarn: false,
    messages: {
      en: {}
    }
  })

const modelComponentStub = (name: string) =>
  defineComponent({
    name,
    props: {
      modelValue: {
        type: [String, Number, Boolean, Array, Object, null],
        default: undefined
      }
    },
    emits: ['update:modelValue', 'change'],
    setup(_, { slots }) {
      return () => h('div', slots.default?.())
    }
  })

const basicComponentStub = (name: string) =>
  defineComponent({
    name,
    setup(_, { slots }) {
      return () => h('div', slots.default?.())
    }
  })

const buttonStub = defineComponent({
  name: 'ElButton',
  emits: ['click'],
  setup(_, { slots, emit }) {
    return () =>
      h(
        'button',
        {
          onClick: () => emit('click')
        },
        slots.default?.()
      )
  }
})

const validateMock = vi.fn(() => Promise.resolve())
const clearValidateMock = vi.fn()

const formStub = defineComponent({
  name: 'ElForm',
  setup(_, { slots, expose }) {
    expose({
      validate: validateMock,
      clearValidate: clearValidateMock
    })

    return () => h('form', slots.default?.())
  }
})

const dialogStub = defineComponent({
  name: 'ElDialog',
  setup(_, { slots }) {
    return () => h('div', [slots.default?.(), slots.footer?.()])
  }
})

const paginationStub = defineComponent({
  name: 'ElPagination',
  emits: ['current-change', 'size-change'],
  setup() {
    return () => h('div')
  }
})

const tableColumnStub = defineComponent({
  name: 'ElTableColumn',
  setup() {
    return () => h('div')
  }
})

describe('IntegrationConfigFilterBar', () => {
  it('emits updates and search/reset actions', async () => {
    const wrapper = mount(IntegrationConfigFilterBar, {
      props: {
        systemType: undefined,
        isEnabled: undefined,
        healthStatus: undefined
      },
      global: {
        plugins: [createTestI18n()],
        stubs: {
          'el-form': basicComponentStub('ElForm'),
          'el-form-item': basicComponentStub('ElFormItem'),
          'el-select': modelComponentStub('ElSelect'),
          'el-option': basicComponentStub('ElOption'),
          'el-button': buttonStub
        }
      }
    })

    const selects = wrapper.findAllComponents({ name: 'ElSelect' })
    selects[0].vm.$emit('update:modelValue', 'sap')
    selects[0].vm.$emit('change')
    selects[1].vm.$emit('update:modelValue', true)
    selects[1].vm.$emit('change')
    selects[2].vm.$emit('update:modelValue', 'healthy')
    selects[2].vm.$emit('change')

    await nextTick()

    expect(wrapper.emitted('update:systemType')?.[0]).toEqual(['sap'])
    expect(wrapper.emitted('update:isEnabled')?.[0]).toEqual([true])
    expect(wrapper.emitted('update:healthStatus')?.[0]).toEqual(['healthy'])
    expect(wrapper.emitted('search')).toHaveLength(3)

    const buttons = wrapper.findAll('button')
    await buttons[1].trigger('click')

    expect(wrapper.emitted('reset')).toHaveLength(1)
  })
})

describe('IntegrationConfigFormDialog', () => {
  beforeEach(() => {
    validateMock.mockReset()
    clearValidateMock.mockReset()
    validateMock.mockResolvedValue()
  })

  it('emits submit payload when form validation succeeds', async () => {
    const formData = createDefaultIntegrationFormData()

    const wrapper = mount(IntegrationConfigFormDialog, {
      props: {
        modelValue: true,
        isEdit: false,
        submitting: false,
        formData
      },
      global: {
        plugins: [createTestI18n()],
        stubs: {
          'el-dialog': dialogStub,
          'el-form': formStub,
          'el-form-item': basicComponentStub('ElFormItem'),
          'el-divider': basicComponentStub('ElDivider'),
          'el-select': modelComponentStub('ElSelect'),
          'el-option': basicComponentStub('ElOption'),
          'el-input': modelComponentStub('ElInput'),
          'el-switch': modelComponentStub('ElSwitch'),
          'el-input-number': modelComponentStub('ElInputNumber'),
          'el-checkbox-group': modelComponentStub('ElCheckboxGroup'),
          'el-checkbox': basicComponentStub('ElCheckbox'),
          'el-button': buttonStub
        }
      }
    })

    const buttons = wrapper.findAll('button')
    await buttons[1].trigger('click')

    expect(validateMock).toHaveBeenCalledTimes(1)
    expect(wrapper.emitted('submit')).toHaveLength(1)
    expect(wrapper.emitted('submit')?.[0]?.[0]).toEqual(formData)
  })

  it('does not emit submit when validation fails', async () => {
    validateMock.mockRejectedValueOnce(new Error('invalid form'))

    const wrapper = mount(IntegrationConfigFormDialog, {
      props: {
        modelValue: true,
        isEdit: false,
        submitting: false,
        formData: createDefaultIntegrationFormData()
      },
      global: {
        plugins: [createTestI18n()],
        stubs: {
          'el-dialog': dialogStub,
          'el-form': formStub,
          'el-form-item': basicComponentStub('ElFormItem'),
          'el-divider': basicComponentStub('ElDivider'),
          'el-select': modelComponentStub('ElSelect'),
          'el-option': basicComponentStub('ElOption'),
          'el-input': modelComponentStub('ElInput'),
          'el-switch': modelComponentStub('ElSwitch'),
          'el-input-number': modelComponentStub('ElInputNumber'),
          'el-checkbox-group': modelComponentStub('ElCheckboxGroup'),
          'el-checkbox': basicComponentStub('ElCheckbox'),
          'el-button': buttonStub
        }
      }
    })

    const buttons = wrapper.findAll('button')
    await buttons[1].trigger('click')

    expect(wrapper.emitted('submit')).toBeUndefined()
  })
})

describe('IntegrationLogsDrawer', () => {
  it('emits refresh and pagination events', async () => {
    const wrapper = mount(IntegrationLogsDrawer, {
      props: {
        modelValue: true,
        currentConfig: {
          id: 'cfg-1',
          systemType: 'sap',
          systemName: 'SAP PROD',
          isEnabled: true,
          enabledModules: ['finance'],
          connectionConfig: {},
          syncConfig: {},
          healthStatus: 'healthy',
          lastSyncAt: null,
          lastSyncStatus: null
        },
        logsLoading: false,
        logs: [],
        page: 1,
        pageSize: 20,
        total: 0
      },
      global: {
        plugins: [createTestI18n()],
        stubs: {
          'el-drawer': basicComponentStub('ElDrawer'),
          'el-button': buttonStub,
          'el-table': basicComponentStub('ElTable'),
          'el-table-column': tableColumnStub,
          'el-tag': basicComponentStub('ElTag'),
          'el-pagination': paginationStub
        },
        directives: {
          loading: () => undefined
        }
      }
    })

    const refreshButton = wrapper.find('button')
    await refreshButton.trigger('click')

    const pagination = wrapper.findComponent({ name: 'ElPagination' })
    pagination.vm.$emit('current-change', 3)
    pagination.vm.$emit('size-change', 50)

    await nextTick()

    expect(wrapper.emitted('refresh')).toHaveLength(1)
    expect(wrapper.emitted('page-change')?.[0]).toEqual([3])
    expect(wrapper.emitted('page-size-change')?.[0]).toEqual([50])
  })
})
