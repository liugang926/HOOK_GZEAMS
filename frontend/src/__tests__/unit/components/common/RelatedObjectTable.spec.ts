/* eslint-disable vue/one-component-per-file */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'

const mockRequest = vi.fn()

vi.mock('@/utils/request', () => ({
  default: mockRequest
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

interface RequestConfig {
  url?: string
  method?: string
  params?: Record<string, unknown>
}

const mountRelatedObjectTable = async () => {
  vi.resetModules()
  const i18n = (await import('@/locales')).default
  const RelatedObjectTable = (await import('@/components/common/RelatedObjectTable.vue')).default

  const wrapper = mount(RelatedObjectTable, {
    props: {
      parentObjectCode: 'Asset',
      parentId: 'asset-1',
      field: {
        code: 'maintenance_records',
        name: 'Maintenance Records',
        label: 'Maintenance Records',
        fieldType: 'reverse_fk',
        reverseRelationModel: 'apps.lifecycle.models.Maintenance',
        reverseRelationField: 'asset'
      },
      mode: 'inline_readonly'
    },
    global: {
      plugins: [i18n],
      stubs: {
        BaseTable: defineComponent({
          name: 'BaseTable',
          props: {
            columns: { type: Array, default: () => [] },
            data: { type: Array, default: () => [] },
            loading: { type: Boolean, default: false }
          },
          template: '<div class="base-table-stub"></div>'
        }),
        'el-button': defineComponent({
          name: 'ElButton',
          template: '<button><slot /></button>'
        }),
        FieldRenderer: defineComponent({
          name: 'FieldRenderer',
          template: '<div class="field-renderer-stub"></div>'
        }),
        'el-input': defineComponent({
          name: 'ElInput',
          template: '<input />'
        }),
        'el-select': defineComponent({
          name: 'ElSelect',
          template: '<select><slot /></select>'
        }),
        'el-option': defineComponent({
          name: 'ElOption',
          template: '<option><slot /></option>'
        }),
        'el-icon': defineComponent({
          name: 'ElIcon',
          template: '<i><slot /></i>'
        }),
        'el-badge': defineComponent({
          name: 'ElBadge',
          template: '<div><slot /></div>'
        }),
        'el-pagination': defineComponent({
          name: 'ElPagination',
          template: '<div></div>'
        })
      }
    }
  })

  await flushPromises()
  return wrapper
}

describe('RelatedObjectTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('builds related columns from the target object list runtime model', async () => {
    mockRequest.mockImplementation((config: RequestConfig) => {
      if (String(config?.url || '').endsWith('/runtime/')) {
        return Promise.resolve({
          runtimeVersion: 1,
          fields: {
            editableFields: [
              { code: 'code', name: 'Code', showInList: true, sortOrder: 1, isSearchable: true },
              { code: 'status', name: 'Status', showInList: true, sortOrder: 2 },
              { code: 'hiddenNote', name: 'Hidden Note', showInList: false, sortOrder: 3 }
            ],
            reverseRelations: []
          },
          layout: {
            layoutConfig: {
              sections: [
                {
                  id: 'list_default',
                  type: 'section',
                  fields: [
                    { fieldCode: 'code', visible: true },
                    { fieldCode: 'status', visible: true }
                  ]
                }
              ]
            }
          },
          permissions: {
            view: true,
            add: true,
            change: true,
            delete: true
          }
        })
      }
      return Promise.resolve({
        count: 1,
        results: [
          { id: 'r-1', code: 'M-001', status: 'done' }
        ]
      })
    })

    const wrapper = await mountRelatedObjectTable()
    const table = wrapper.findComponent({ name: 'BaseTable' })
    const columns = (table.props('columns') || []) as Array<{ prop: string }>
    const props = columns.map((col) => col.prop)

    expect(mockRequest).toHaveBeenCalledWith(expect.objectContaining({
      url: '/system/objects/Maintenance/runtime/',
      method: 'get',
      params: expect.objectContaining({
        mode: 'list',
        include_relations: false
      })
    }))
    expect(props).toContain('code')
    expect(props).toContain('status')
    expect(props).not.toContain('id')
    expect(props).not.toContain('hiddenNote')
  })

  it('falls back to record keys when runtime metadata is unavailable', async () => {
    mockRequest.mockImplementation((config: RequestConfig) => {
      const url = String(config?.url || '')
      if (url.endsWith('/runtime/') || url.endsWith('/fields/')) {
        return Promise.reject(new Error('metadata failed'))
      }
      return Promise.resolve({
        count: 1,
        results: [
          { id: 'r-2', code: 'M-002', name: 'Repair', createdAt: '2026-03-03T00:00:00Z' }
        ]
      })
    })

    const wrapper = await mountRelatedObjectTable()
    const table = wrapper.findComponent({ name: 'BaseTable' })
    const columns = (table.props('columns') || []) as Array<{ prop: string }>
    const props = columns.map((col) => col.prop)

    expect(props).toContain('code')
    expect(props).toContain('name')
    expect(props).toContain('createdAt')
    expect(props).not.toContain('id')
    // Ensure no object-specific hardcoded template column leaked in fallback.
    expect(props).not.toContain('maintenanceType')
  })

  it('localizes object-style column labels from runtime metadata', async () => {
    mockRequest.mockImplementation((config: RequestConfig) => {
      if (String(config?.url || '').endsWith('/runtime/')) {
        return Promise.resolve({
          runtimeVersion: 1,
          fields: {
            editableFields: [
              {
                code: 'asset',
                label: { 'zh-cn': '资产', 'en-us': 'Asset' },
                fieldType: 'asset',
                showInList: true,
                sortOrder: 1
              }
            ],
            reverseRelations: []
          },
          layout: {
            layoutConfig: {
              sections: [
                {
                  id: 'list_default',
                  type: 'section',
                  fields: [
                    { fieldCode: 'asset', visible: true }
                  ]
                }
              ]
            }
          },
          permissions: {
            view: true,
            add: true,
            change: true,
            delete: true
          }
        })
      }
      return Promise.resolve({
        count: 1,
        results: [
          { id: 'r-3', asset: { id: 'a-1', name: 'Laptop 01' } }
        ]
      })
    })

    const wrapper = await mountRelatedObjectTable()
    const table = wrapper.findComponent({ name: 'BaseTable' })
    const columns = (table.props('columns') || []) as Array<{ prop: string; label: string }>

    expect(columns).toHaveLength(1)
    expect(columns[0].prop).toBe('asset')
    expect(columns[0].label).not.toBe('[object Object]')
    expect(['Asset', '资产']).toContain(columns[0].label)
  })
})
