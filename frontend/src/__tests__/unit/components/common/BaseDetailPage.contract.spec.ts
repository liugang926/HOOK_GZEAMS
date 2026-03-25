import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'

const getRelationsMock = vi.fn()

vi.mock('@/api/dynamic', () => ({
  dynamicApi: {
    getRelations: getRelationsMock
  }
}))

const mountPage = async (
  propOverrides: Record<string, any> = {},
  slotOverrides: Record<string, any> = {}
) => {
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
        collapsible: true,
        fields: [
          { prop: 'name', label: 'Name' }
        ]
      }
    ],
    loading: false,
    extraActions: [
      {
        label: 'Archive',
        action: vi.fn()
      }
    ]
  }

  const wrapper = mount(BaseDetailPage, {
    props: {
      ...defaultProps,
      ...propOverrides
    },
    slots: slotOverrides,
    global: {
      plugins: [i18n],
      stubs: {
        RelatedObjectTable: defineComponent({
          name: 'RelatedObjectTable',
          template: '<div class="related-table-stub"></div>'
        }),
        ActivityTimeline: defineComponent({
          name: 'ActivityTimeline',
          props: ['objectCode', 'recordId'],
          template: '<div class="activity-timeline-stub">{{ objectCode }}::{{ recordId }}</div>'
        }),
        FieldDisplay: defineComponent({
          name: 'FieldDisplay',
          props: { value: { type: null, default: null } },
          template: '<span class="field-display-stub">{{ value }}</span>'
        }),
        ObjectAvatar: defineComponent({
          name: 'ObjectAvatar',
          template: '<div class="object-avatar-stub"></div>'
        }),
        ErrorBoundary: defineComponent({
          name: 'ErrorBoundary',
          template: '<div><slot /></div>'
        }),
        FieldRenderer: defineComponent({
          name: 'FieldRenderer',
          props: ['field', 'modelValue', 'disabled'],
          emits: ['update:modelValue'],
          template: '<input class="field-renderer-stub" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />'
        }),
        'el-button': defineComponent({
          name: 'ElButton',
          emits: ['click'],
          template: '<button @click="$emit(\'click\')"><slot /></button>'
        }),
        'el-form': defineComponent({
          name: 'ElForm',
          props: ['model', 'rules'],
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
        'el-empty': defineComponent({
          name: 'ElEmpty',
          template: '<div class="el-empty-stub"></div>'
        }),
        'el-descriptions': defineComponent({
          name: 'ElDescriptions',
          template: '<div class="el-descriptions-stub"><slot /></div>'
        }),
        'el-descriptions-item': defineComponent({
          name: 'ElDescriptionsItem',
          template: '<div class="el-descriptions-item-stub"><slot /></div>'
        }),
        'el-tag': defineComponent({
          name: 'ElTag',
          template: '<span><slot /></span>'
        }),
        'el-tabs': defineComponent({
          name: 'ElTabs',
          props: ['modelValue'],
          emits: ['update:modelValue', 'tab-change'],
          template: '<div class="el-tabs-stub"><slot /></div>'
        }),
        'el-tab-pane': defineComponent({
          name: 'ElTabPane',
          props: ['label'],
          template: '<div class="el-tab-pane-stub"><span class="tab-label-stub">{{ label }}</span><slot /></div>'
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

describe('BaseDetailPage contract', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getRelationsMock.mockResolvedValue({ relations: [] })
  })

  it('renders the original header structure and audit info/actions contract', async () => {
    const wrapper = await mountPage({
      auditInfo: {
        updatedBy: 'alice',
        updatedAt: '2026-03-07T10:00:00Z'
      }
    }, {
      'action-bar': () => h('div', { class: 'toolbar-slot-stub' }, 'toolbar')
    })

    expect(wrapper.find('.record-profile-header').exists()).toBe(true)
    expect(wrapper.find('.header-left').exists()).toBe(true)
    expect(wrapper.find('.profile-identity').exists()).toBe(true)
    expect(wrapper.find('.header-right').exists()).toBe(true)
    expect(wrapper.find('.header-audit-info').text()).toContain('alice')
    expect(wrapper.find('.toolbar-slot-stub').exists()).toBe(true)
    expect(wrapper.text()).toContain('编辑')
    expect(wrapper.text()).toContain('删除')
  })

  it('keeps section-click wired through the parent contract and toggles collapse', async () => {
    const wrapper = await mountPage()

    await wrapper.find('.section-header').trigger('click')
    await nextTick()

    expect(wrapper.emitted('section-click')).toEqual([['basic']])
    expect(wrapper.find('.detail-section').classes()).toContain('is-collapsed')
  })

  it('passes resolved field value into field slots', async () => {
    const wrapper = await mountPage({
      sections: [
        {
          name: 'basic',
          title: 'Basic',
          fields: [
            { prop: 'name', label: 'Name', type: 'slot' }
          ]
        }
      ]
    }, {
      'field-name': ({ value }: any) => h('div', { class: 'field-slot-value' }, String(value))
    })

    expect(wrapper.find('.field-slot-value').text()).toBe('Org One')
  })

  it('renders the change history tab when object code and record id are available', async () => {
    const wrapper = await mountPage()

    expect(wrapper.text()).toContain('变更记录')
    expect(wrapper.text()).toContain('Organization::org-1')
  })
  it('builds runtime validation rules from layout field config in edit mode', async () => {
    const wrapper = await mountPage({
      editMode: true,
      formData: {
        name: ''
      },
      sections: [
        {
          name: 'basic',
          title: 'Basic',
          fields: [
            {
              prop: 'name',
              label: 'Name',
              required: true,
              min_length: 2,
              max_length: 10,
              regex_pattern: '^[A-Z].*$'
            }
          ]
        }
      ]
    })

    const form = wrapper.findComponent({ name: 'ElForm' })
    const rules = form.props('rules') as Record<string, any[]>

    expect(Array.isArray(rules.name)).toBe(true)
    expect(rules.name).toHaveLength(4)
  })

  it('skips generated validation rules for hidden fields', async () => {
    const wrapper = await mountPage({
      editMode: true,
      formData: {
        secret: ''
      },
      sections: [
        {
          name: 'basic',
          title: 'Basic',
          fields: [
            {
              prop: 'secret',
              label: 'Secret',
              required: true,
              hidden: true
            }
          ]
        }
      ]
    })

    const form = wrapper.findComponent({ name: 'ElForm' })
    const rules = form.props('rules') as Record<string, any[]>

    expect(rules.secret).toBeUndefined()
  })

  it('evaluates visibility rules against form data and skips hidden-by-rule validation', async () => {
    const wrapper = await mountPage({
      editMode: true,
      formData: {
        status: 'draft',
        publishNote: ''
      },
      sections: [
        {
          name: 'basic',
          title: 'Basic',
          fields: [
            {
              prop: 'status',
              label: 'Status'
            },
            {
              prop: 'publishNote',
              label: 'Publish Note',
              required: true,
              visibilityRule: {
                field: 'status',
                operator: 'eq',
                value: 'published'
              }
            }
          ]
        }
      ]
    })

    const form = wrapper.findComponent({ name: 'ElForm' })
    const rules = form.props('rules') as Record<string, any[]>

    expect(rules.publishNote).toBeUndefined()
    expect(wrapper.text()).not.toContain('Publish Note')
  })
})
