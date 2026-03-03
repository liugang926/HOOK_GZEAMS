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

  it('builds related columns from metadata list fields', async () => {
    mockRequest.mockImplementation((config: RequestConfig) => {
      if (String(config?.url || '').endsWith('/fields/')) {
        return Promise.resolve({
          editableFields: [
            { code: 'code', name: 'Code', showInList: true, sortOrder: 1 },
            { code: 'status', name: 'Status', showInList: true, sortOrder: 2 },
            { code: 'hidden_note', name: 'Hidden Note', showInList: false, sortOrder: 3 }
          ],
          reverseRelations: [],
          context: 'list'
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
      url: '/system/objects/Maintenance/fields/',
      method: 'get',
      params: expect.objectContaining({
        context: 'list',
        include_relations: false
      })
    }))
    expect(props).toContain('id')
    expect(props).toContain('code')
    expect(props).toContain('status')
    expect(props).not.toContain('hidden_note')
  })

  it('falls back to record keys when metadata is unavailable', async () => {
    mockRequest.mockImplementation((config: RequestConfig) => {
      if (String(config?.url || '').endsWith('/fields/')) {
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

    expect(props).toContain('id')
    expect(props).toContain('code')
    expect(props).toContain('name')
    expect(props).toContain('createdAt')
    // Ensure no object-specific hardcoded template column leaked in fallback.
    expect(props).not.toContain('maintenanceType')
  })
})
