/**
 * SectionBlock component tests
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import SectionBlock from '@/components/common/SectionBlock.vue'

// Mock Element Plus components
vi.mock('element-plus', () => ({
  ElIcon: {
    name: 'ElIcon',
    template: '<div class="el-icon"><slot /></div>'
  },
  ElTag: {
    name: 'ElTag',
    template: '<div class="el-tag"><slot /></div>',
    props: ['type', 'size']
  },
  ElTooltip: {
    name: 'ElTooltip',
    template: '<div class="el-tooltip"><slot /></div>',
    props: ['content', 'placement']
  },
  ElCollapseTransition: {
    name: 'ElCollapseTransition',
    template: '<div class="el-collapse-transition"><slot /></div>'
  }
}))

// Mock icons
vi.mock('@element-plus/icons-vue', () => ({
  ArrowDown: { template: '<svg />' },
  InfoFilled: { template: '<svg />' }
}))

describe('SectionBlock', () => {
  it('should render section with title', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test Section'
      }
    })

    expect(wrapper.find('.section-block').exists()).toBe(true)
    expect(wrapper.text()).toContain('Test Section')
  })

  it('should have correct default props', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test'
      }
    })

    const vm = wrapper.vm as any
    expect(vm.collapsed).toBe(false)
    expect(vm.collapsible).toBe(true)
    expect(vm.variant).toBe('default')
    expect(vm.size).toBe('medium')
    expect(vm.noBorder).toBe(false)
    expect(vm.noPadding).toBe(false)
  })

  it('should render collapse icon when collapsible', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Collapsible Section',
        collapsible: true
      }
    })

    expect(wrapper.find('.collapse-icon').exists()).toBe(true)
  })

  it('should not render collapse icon when not collapsible', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Non-collapsible Section',
        collapsible: false
      }
    })

    expect(wrapper.find('.collapse-icon').exists()).toBe(false)
  })

  it('should toggle collapsed state', async () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Toggle Section'
      }
    })

    const vm = wrapper.vm as any
    expect(vm.isCollapsed).toBe(false)

    vm.toggle()
    await nextTick()

    expect(vm.isCollapsed).toBe(true)
    expect(wrapper.emitted('collapse')).toBeTruthy()
    expect(wrapper.emitted('toggle')).toBeTruthy()
  })

  it('should not toggle when not collapsible', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Non-collapsible',
        collapsible: false
      }
    })

    const vm = wrapper.vm as any
    vm.toggle()

    expect(vm.isCollapsed).toBe(false)
  })

  it('should emit update:modelValue when v-model used', async () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test',
        modelValue: false
      }
    })

    const vm = wrapper.vm as any
    vm.toggle()
    await nextTick()

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([true])
  })

  it('should sync isCollapsed with modelValue prop changes', async () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test',
        modelValue: false
      }
    })

    const vm = wrapper.vm as any
    expect(vm.isCollapsed).toBe(false)

    await wrapper.setProps({ modelValue: true })
    await nextTick()

    expect(vm.isCollapsed).toBe(true)
  })

  it('should sync isCollapsed with collapsed prop changes', async () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test',
        collapsed: false
      }
    })

    const vm = wrapper.vm as any
    expect(vm.isCollapsed).toBe(false)

    await wrapper.setProps({ collapsed: true })
    await nextTick()

    expect(vm.isCollapsed).toBe(true)
  })

  it('should render tag when provided', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Section with Tag',
        tag: 'New'
      }
    })

    expect(wrapper.find('.title-tag').exists()).toBe(true)
  })

  it('should show tooltip when provided', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Section with Tooltip',
        tooltip: 'Help text'
      }
    })

    const vm = wrapper.vm as any
    expect(vm.showTooltip).toBe(true)
  })

  it('should apply variant class', () => {
    const variants: Array<'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = [
      'default', 'primary', 'success', 'warning', 'danger', 'info'
    ]

    variants.forEach(variant => {
      const wrapper = mount(SectionBlock, {
        props: {
          title: 'Test',
          variant
        }
      })

      expect(wrapper.find(`.section-${variant}`).exists()).toBe(true)
    })
  })

  it('should apply size class', () => {
    const sizes: Array<'small' | 'medium' | 'large'> = ['small', 'medium', 'large']

    sizes.forEach(size => {
      const wrapper = mount(SectionBlock, {
        props: {
          title: 'Test',
          size
        }
      })

      expect(wrapper.find(`.section-${size}`).exists()).toBe(true)
    })
  })

  it('should apply no-border class when noBorder is true', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test',
        noBorder: true
      }
    })

    expect(wrapper.find('.no-border').exists()).toBe(true)
  })

  it('should apply no-padding class when noPadding is true', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test',
        noPadding: true
      }
    })

    expect(wrapper.find('.section-body.no-padding').exists()).toBe(true)
  })

  it('should apply header-no-padding class when headerNoPadding is true', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test',
        headerNoPadding: true
      }
    })

    expect(wrapper.find('.section-header.no-padding').exists()).toBe(true)
  })

  it('should render footer slot when provided', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test'
      },
      slots: {
        footer: '<div class="footer-content">Footer Content</div>'
      }
    })

    expect(wrapper.find('.section-footer').exists()).toBe(true)
    expect(wrapper.find('.footer-content').exists()).toBe(true)
  })

  it('should not render footer when slot not provided', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test'
      }
    })

    expect(wrapper.find('.section-footer').exists()).toBe(false)
  })

  it('should render actions slot when provided', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test'
      },
      slots: {
        actions: '<button class="action-btn">Action</button>'
      }
    })

    expect(wrapper.find('.actions').exists()).toBe(true)
    expect(wrapper.find('.action-btn').exists()).toBe(true)
  })

  it('should render default slot content', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test'
      },
      slots: {
        default: '<div class="body-content">Body Content</div>'
      }
    })

    expect(wrapper.find('.body-content').exists()).toBe(true)
  })

  it('should render body slot when provided', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test'
      },
      slots: {
        body: '<div class="custom-body">Custom Body</div>'
      }
    })

    expect(wrapper.find('.custom-body').exists()).toBe(true)
  })

  it('should add is-collapsed class when collapsed', async () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test'
      }
    })

    const vm = wrapper.vm as any
    vm.isCollapsed = true
    await nextTick()

    expect(wrapper.find('.is-collapsed').exists()).toBe(true)
  })

  it('should add clickable class to header when collapsible', () => {
    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test',
        collapsible: true
      }
    })

    expect(wrapper.find('.section-header.clickable').exists()).toBe(true)
  })

  it('should render custom icon when provided', () => {
    const CustomIcon = { template: '<svg>ICON</svg>' }

    const wrapper = mount(SectionBlock, {
      props: {
        title: 'Test',
        icon: CustomIcon
      }
    })

    const vm = wrapper.vm as any
    expect(vm.icon).toBeDefined()
  })
})
