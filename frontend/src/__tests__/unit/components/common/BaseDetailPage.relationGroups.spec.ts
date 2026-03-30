import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'

const getRelationsMock = vi.fn()

vi.mock('@/api/dynamic', () => ({
  dynamicApi: {
    getRelations: getRelationsMock
  }
}))

const relationRows = [
  {
    relationCode: 'workflow_instances',
    relationName: 'Workflow Instances',
    targetObjectCode: 'WorkflowInstance',
    displayMode: 'inline_readonly',
    sortOrder: 10,
    groupKey: 'workflow',
    groupName: 'Workflow',
    groupOrder: 20,
    defaultExpanded: true
  },
  {
    relationCode: 'finance_vouchers',
    relationName: 'Finance Vouchers',
    targetObjectCode: 'FinanceVoucher',
    displayMode: 'inline_readonly',
    sortOrder: 20,
    groupKey: 'finance',
    groupName: 'Finance',
    groupOrder: 30,
    defaultExpanded: false
  }
]

const memoryStorage = new Map<string, string>()

const storageGet = (key: string) => memoryStorage.get(key) ?? null
const storageSet = (key: string, value: string) => {
  memoryStorage.set(key, String(value))
}
const storageRemove = (key: string) => {
  memoryStorage.delete(key)
}

const mountPage = async (propOverrides: Record<string, any> = {}) => {
  vi.resetModules()
  const i18n = (await import('@/locales')).default
  const BaseDetailPage = (await import('@/components/common/BaseDetailPage.vue')).default

  const defaultProps = {
    title: 'Organization Detail',
    objectCode: 'Organization',
    objectName: 'Organization',
    data: {
      id: 'org-1',
      name: 'Org One'
    },
    sections: [
      {
        name: 'basic',
        title: 'Basic',
        fields: [
          { prop: 'name', label: 'Name' }
        ]
      }
    ],
    loading: false
  }

  const wrapper = mount(BaseDetailPage, {
    props: {
      ...defaultProps,
      ...propOverrides
    },
    global: {
      plugins: [i18n],
      stubs: {
        RelatedObjectTable: defineComponent({
          name: 'RelatedObjectTable',
          template: '<div class="related-table-stub"></div>'
        }),
        ActivityTimeline: defineComponent({
          name: 'ActivityTimeline',
          template: '<div class="activity-timeline-stub"></div>'
        }),
        FieldDisplay: defineComponent({
          name: 'FieldDisplay',
          props: { value: { type: null, default: null } },
          template: '<span class="field-display-stub">{{ value }}</span>'
        }),
        ObjectAvatar: true,
        ErrorBoundary: defineComponent({
          name: 'ErrorBoundary',
          template: '<div><slot /></div>'
        }),
        FieldRenderer: true,
        'el-button': defineComponent({
          name: 'ElButton',
          emits: ['click'],
          template: '<button @click="$emit(\'click\')"><slot /></button>'
        }),
        'el-form': defineComponent({
          name: 'ElForm',
          template: '<form><slot /></form>'
        }),
        'el-form-item': defineComponent({
          name: 'ElFormItem',
          template: '<div><slot /></div>'
        }),
        'el-icon': defineComponent({
          name: 'ElIcon',
          template: '<i><slot /></i>'
        }),
        'el-empty': true,
        'el-descriptions': defineComponent({
          name: 'ElDescriptions',
          template: '<div><slot /></div>'
        }),
        'el-descriptions-item': defineComponent({
          name: 'ElDescriptionsItem',
          template: '<div><slot /></div>'
        }),
        'el-tag': defineComponent({
          name: 'ElTag',
          template: '<span><slot /></span>'
        }),
        'el-tabs': defineComponent({
          name: 'ElTabs',
          template: '<div><slot /></div>'
        }),
        'el-tab-pane': defineComponent({
          name: 'ElTabPane',
          template: '<div><slot /></div>'
        }),
        'el-skeleton': defineComponent({
          name: 'ElSkeleton',
          template: '<div><slot name="template" /></div>'
        }),
        'el-skeleton-item': true,
        'el-alert': defineComponent({
          name: 'ElAlert',
          template: '<div><slot /></div>'
        })
      }
    }
  })

  await flushPromises()
  await nextTick()
  return wrapper
}

const getGroupByTitle = (wrapper: ReturnType<typeof mount>, title: string) => {
  return wrapper.findAll('.related-group-item').find((node) => node.text().includes(title))
}

describe('BaseDetailPage relation groups', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    memoryStorage.clear()
    ;(localStorage.getItem as any).mockImplementation((key: string) => storageGet(key))
    ;(localStorage.setItem as any).mockImplementation((key: string, value: string) => storageSet(key, value))
    ;(localStorage.removeItem as any).mockImplementation((key: string) => storageRemove(key))
    getRelationsMock.mockResolvedValue({ relations: relationRows })
  })

  it('persists expanded groups and restores them for same record scope', async () => {
    const wrapper = await mountPage()

    const workflow = getGroupByTitle(wrapper, 'Workflow')
    const finance = getGroupByTitle(wrapper, 'Finance')
    expect(workflow).toBeTruthy()
    expect(finance).toBeTruthy()
    expect(workflow!.classes()).toContain('is-active')
    expect(finance!.classes()).not.toContain('is-active')
    expect(workflow!.find('.related-group-header').attributes('aria-expanded')).toBe('true')
    expect(finance!.find('.related-group-header').attributes('aria-expanded')).toBe('false')
    expect(workflow!.find('.related-group-header').attributes('aria-controls')).toContain('related-group-panel-')
    expect(finance!.find('.related-group-header').attributes('aria-controls')).toContain('related-group-panel-')

    await finance!.find('.related-group-header').trigger('click')
    await workflow!.find('.related-group-header').trigger('click')
    await flushPromises()

    expect(workflow!.classes()).not.toContain('is-active')
    expect(finance!.classes()).toContain('is-active')
    expect(workflow!.find('.related-group-header').attributes('aria-expanded')).toBe('false')
    expect(finance!.find('.related-group-header').attributes('aria-expanded')).toBe('true')

    const storageKey = 'gzeams:detail:related-groups:Organization:org-1'
    const stored = memoryStorage.get(storageKey)
    expect(stored).toBeTruthy()
    expect(stored).toContain('"finance"')
    expect(stored).not.toContain('"workflow"')

    wrapper.unmount()

    const wrapper2 = await mountPage()
    const workflow2 = getGroupByTitle(wrapper2, 'Workflow')
    const finance2 = getGroupByTitle(wrapper2, 'Finance')
    expect(workflow2).toBeTruthy()
    expect(finance2).toBeTruthy()
    expect(workflow2!.classes()).not.toContain('is-active')
    expect(finance2!.classes()).toContain('is-active')
    expect(workflow2!.find('.related-group-header').attributes('aria-expanded')).toBe('false')
    expect(finance2!.find('.related-group-header').attributes('aria-expanded')).toBe('true')

    wrapper2.unmount()
  })

  it('uses relationGroupScopeId when record id is unavailable', async () => {
    const scopedKey = 'gzeams:detail:related-groups:Organization:designer-preview:edit:draft'
    memoryStorage.set(scopedKey, JSON.stringify({ expanded: ['finance'] }))

    const wrapper = await mountPage({
      data: {
        name: 'Org Without Id'
      },
      relationGroupScopeId: 'designer-preview:edit:draft'
    })

    const workflow = getGroupByTitle(wrapper, 'Workflow')
    const finance = getGroupByTitle(wrapper, 'Finance')
    expect(workflow).toBeTruthy()
    expect(finance).toBeTruthy()
    expect(workflow!.classes()).not.toContain('is-active')
    expect(finance!.classes()).toContain('is-active')

    await workflow!.find('.related-group-header').trigger('click')
    await flushPromises()

    const stored = memoryStorage.get(scopedKey)
    expect(stored).toBeTruthy()
    expect(stored).toContain('"finance"')
    expect(stored).toContain('"workflow"')

    wrapper.unmount()
  })
})
