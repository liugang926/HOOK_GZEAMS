import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'

const ElTabsStub = defineComponent({
  name: 'ElTabs',
  props: {
    modelValue: {
      type: String,
      default: ''
    }
  },
  emits: ['update:modelValue'],
  template: `
    <div class="el-tabs-stub">
      <button class="switch-tab" @click="$emit('update:modelValue', 'tab-2')">switch</button>
      <slot />
    </div>
  `
})

const mountRenderer = async (props: Record<string, any>, slots: Record<string, any> = {}) => {
  const i18n = (await import('@/locales')).default
  const DetailSectionRenderer = (await import('@/components/common/detail/DetailSectionRenderer.vue')).default

  return mount(DetailSectionRenderer, {
    props,
    slots,
    global: {
      plugins: [i18n],
      stubs: {
        ErrorBoundary: defineComponent({
          name: 'ErrorBoundary',
          template: '<div><slot /></div>'
        }),
        'el-icon': defineComponent({
          name: 'ElIcon',
          template: '<i><slot /></i>'
        }),
        'el-tabs': ElTabsStub,
        'el-tab-pane': defineComponent({
          name: 'ElTabPane',
          template: '<div class="el-tab-pane-stub"><slot /></div>'
        }),
        'el-alert': defineComponent({
          name: 'ElAlert',
          template: '<div><slot /></div>'
        }),
        'el-button': defineComponent({
          name: 'ElButton',
          emits: ['click'],
          template: '<button @click="$emit(\'click\')"><slot /></button>'
        }),
        ArrowDown: true
      }
    }
  })
}

describe('DetailSectionRenderer contract', () => {
  it('forwards section header clicks with the full section object and test id', async () => {
    const section = {
      name: 'basic',
      title: 'Basic',
      collapsible: true,
      fields: [{ prop: 'name', label: 'Name' }]
    }

    const wrapper = await mountRenderer({
      section,
      data: { name: 'Org One' },
      displayTitle: 'Basic',
      sectionHeaderTestId: 'layout-section-header'
    }, {
      'field-content': ({ field }: any) => h('span', field.label)
    })

    const header = wrapper.get('[data-testid="layout-section-header"]')
    await header.trigger('click')

    expect(wrapper.emitted('section-click')).toEqual([[section]])
    expect(header.text()).toContain('Basic')
  })

  it('resolves multilingual section titles from translation payload objects', async () => {
    const wrapper = await mountRenderer({
      section: {
        name: 'basic',
        title: { translationKey: 'system.pageLayout.sections.basic' },
        fields: [{ prop: 'name', label: 'Name' }]
      },
      data: { name: 'Org One' }
    }, {
      'field-content': ({ field }: any) => h('span', field.label)
    })

    expect(wrapper.text()).not.toContain('[object Object]')
    expect(wrapper.text()).toContain('基本信息')
  })

  it('passes resolved value into field slots', async () => {
    const wrapper = await mountRenderer({
      section: {
        name: 'basic',
        title: 'Basic',
        fields: [{ prop: 'name', label: 'Name', type: 'slot' }]
      },
      data: { name: 'Org One' },
      getFieldValue: () => 'Org One'
    }, {
      'field-name': ({ value }: any) => h('div', { class: 'slot-value' }, value)
    })

    expect(wrapper.get('.slot-value').text()).toBe('Org One')
  })

  it('emits tab-change through the controlled tab contract', async () => {
    const wrapper = await mountRenderer({
      section: {
        name: 'basic',
        title: 'Basic',
        type: 'tab',
        tabs: [
          { id: 'tab-1', title: 'Tab 1', fields: [] },
          { id: 'tab-2', title: 'Tab 2', fields: [] }
        ],
        fields: []
      },
      data: {},
      activeTabId: 'tab-1'
    })

    await wrapper.get('.switch-tab').trigger('click')
    await nextTick()

    expect(wrapper.emitted('tab-change')).toEqual([['tab-2', 'basic']])
  })
})
