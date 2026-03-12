import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent } from 'vue'

vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn()
  }
}))

vi.mock('@/platform/reference/referenceResolver', () => ({
  referenceResolver: {
    resolve: vi.fn()
  }
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    userInfo: { id: 'user-1' }
  })
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    warning: vi.fn()
  }
}))

import request from '@/utils/request'
import { referenceResolver } from '@/platform/reference/referenceResolver'
import { ElMessage } from 'element-plus'

const ElSelectStub = defineComponent({
  name: 'ElSelect',
  emits: ['update:modelValue', 'visible-change'],
  template: `
    <div class="el-select-stub">
      <button class="open-select" @click="$emit('visible-change', true)">open</button>
      <button class="select-asset-1" @click="$emit('update:modelValue', 'asset-1')">asset-1</button>
      <button class="select-asset-2" @click="$emit('update:modelValue', 'asset-2')">asset-2</button>
      <slot />
    </div>
  `
})

const ElOptionStub = defineComponent({
  name: 'ElOption',
  props: {
    label: { type: String, default: '' },
    value: { type: String, default: '' }
  },
  template: '<div class="el-option-stub" :data-value="value">{{ label }}<slot /></div>'
})

describe('AssetSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(request.get).mockResolvedValue({
      data: {
        results: [
          {
            id: 'asset-1',
            assetCode: 'A-001',
            assetName: 'Laptop A',
            specification: '16G/512G',
            location: 'loc-1',
            locationPath: 'HQ / Floor 1',
            custodian: 'user-2',
            department: 'dept-1',
            assetStatus: 'idle'
          },
          {
            id: 'asset-2',
            assetCode: 'A-002',
            assetName: 'Laptop B',
            specification: '32G/1T',
            location: 'loc-2',
            locationPath: 'HQ / Floor 2',
            custodian: 'user-3',
            department: 'dept-1',
            assetStatus: 'idle'
          }
        ]
      }
    } as any)
    vi.mocked(referenceResolver.resolve).mockResolvedValue(null as any)
  })

  const mountSelector = async (options: {
    row?: Record<string, any>
    rows?: Array<Record<string, any>>
    field?: Record<string, any>
    modelValue?: any
  } = {}) => {
    const AssetSelector = (await import('@/components/engine/fields/AssetSelector.vue')).default
    const row = options.row || { asset: null }
    const rows = options.rows || [row]
    return mount(AssetSelector, {
      props: {
        field: options.field || {
          componentProps: {
            filters: {
              department: { fromParent: ['from_department', 'fromDepartment'] }
            },
            autoFillMappings: {
              assetCode: 'assetCode',
              assetName: 'assetName',
              specification: 'specification',
              location: 'fromLocation'
            }
          }
        },
        formData: {
          __parent: {
            from_department: 'dept-1'
          },
          __row: row,
          __rows: rows
        },
        modelValue: options.modelValue ?? null
      },
      global: {
        stubs: {
          'el-select': ElSelectStub,
          'el-option': ElOptionStub
        },
        mocks: {
          $t: (key: string) => key
        }
      }
    })
  }

  it('applies parent-context filters when loading asset options', async () => {
    const wrapper = await mountSelector()

    await wrapper.find('.open-select').trigger('click')
    await flushPromises()

    expect(request.get).toHaveBeenCalledWith('/system/objects/Asset/', {
      params: expect.objectContaining({
        department: 'dept-1',
        page: 1,
        page_size: 20
      }),
      silent: true
    })
  })

  it('prevents selecting an asset that is already chosen in another row', async () => {
    const currentRow = { asset: null }
    const wrapper = await mountSelector({
      row: currentRow,
      rows: [currentRow, { asset: 'asset-2' }]
    })

    await wrapper.find('.open-select').trigger('click')
    await flushPromises()
    await wrapper.find('.select-asset-2').trigger('click')

    expect(ElMessage.warning).toHaveBeenCalledTimes(1)
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('autofills sibling row fields when an asset is selected', async () => {
    const row = {
      asset: null,
      assetCode: '',
      assetName: '',
      specification: '',
      fromLocation: ''
    }
    const wrapper = await mountSelector({ row, rows: [row] })

    await wrapper.find('.open-select').trigger('click')
    await flushPromises()
    await wrapper.find('.select-asset-1').trigger('click')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['asset-1'])
    expect(row.assetCode).toBe('A-001')
    expect(row.assetName).toBe('Laptop A')
    expect(row.specification).toBe('16G/512G')
    expect(row.fromLocation).toBe('loc-1')
  })
})
