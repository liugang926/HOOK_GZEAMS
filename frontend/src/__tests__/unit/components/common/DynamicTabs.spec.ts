/**
 * DynamicTabs component tests
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick, markRaw } from 'vue'
import DynamicTabs from '@/components/common/DynamicTabs.vue'
import type { TabItem } from '@/types/common'

// Mock Element Plus components
vi.mock('element-plus', () => ({
  ElTabs: {
    name: 'ElTabs',
    template: `
      <div class="el-tabs">
        <slot />
      </div>
    `,
    props: ['modelValue', 'type', 'position', 'stretch', 'animated', 'addable', 'editable', 'closable', 'tabPosition'],
    emits: ['update:modelValue', 'tab-remove', 'tab-add', 'tab-change', 'edit']
  },
  ElTabPane: {
    name: 'ElTabPane',
    template: `
      <div class="el-tab-pane">
        <slot name="label" />
        <slot />
      </div>
    `,
    props: ['name', 'closable', 'disabled', 'lazy']
  },
  ElIcon: {
    name: 'ElIcon',
    template: '<div class="el-icon"><slot /></div>'
  },
  ElBadge: {
    name: 'ElBadge',
    template: '<div class="el-badge"><slot /></div>',
    props: ['value', 'type']
  }
}))

describe('DynamicTabs', () => {
  const mockTabs: TabItem[] = [
    { id: 'tab1', name: 'Tab 1', title: 'First Tab' },
    { id: 'tab2', name: 'Tab 2', title: 'Second Tab' },
    { id: 'tab3', name: 'Tab 3', title: 'Third Tab', closable: true }
  ]

  it('should render tabs correctly', () => {
    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: mockTabs
      }
    })

    // Component should mount successfully
    expect(wrapper.vm).toBeTruthy()
  })

  it('should filter visible tabs', () => {
    const tabsWithHidden: TabItem[] = [
      ...mockTabs,
      { id: 'tab4', name: 'Tab 4', title: 'Hidden Tab', visible: false }
    ]

    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: tabsWithHidden
      }
    })

    // Visible tabs should not include the hidden one
    const visibleCount = tabsWithHidden.filter(tab => tab.visible !== false).length
    expect(visibleCount).toBe(3)

    // Verify through component state
    const vm = wrapper.vm as any
    expect(vm.visibleTabs).toHaveLength(3)
  })

  it('should compute hasClosableTabs correctly', () => {
    const tabsWithoutClosable: TabItem[] = [
      { id: 'tab1', name: 'Tab 1', title: 'First Tab', closable: false },
      { id: 'tab2', name: 'Tab 2', title: 'Second Tab', closable: false }
    ]

    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: tabsWithoutClosable
      }
    })

    const vm = wrapper.vm as any
    expect(vm.hasClosableTabs).toBe(false)

    const wrapper2 = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: mockTabs
      }
    })

    const vm2 = wrapper2.vm as any
    expect(vm2.hasClosableTabs).toBe(true)
  })

  it('should have correct default props', () => {
    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: []
      }
    })

    const vm = wrapper.vm as any
    expect(vm.position).toBe('top')
    expect(vm.typeStyle).toBe('')
    expect(vm.stretch).toBe(false)
    expect(vm.animated).toBe(true)
    expect(vm.addable).toBe(false)
    expect(vm.editable).toBe(false)
  })

  it('should accept custom position', () => {
    const positions: Array<'top' | 'left' | 'right' | 'bottom'> = ['top', 'left', 'right', 'bottom']

    positions.forEach(position => {
      const wrapper = mount(DynamicTabs, {
        props: {
          modelValue: 'tab1',
          tabs: mockTabs,
          position
        }
      })

      expect((wrapper.vm as any).position).toBe(position)
    })
  })

  it('should accept custom type style', () => {
    const typeStyles: Array<'' | 'card' | 'border-card'> = ['', 'card', 'border-card']

    typeStyles.forEach(typeStyle => {
      const wrapper = mount(DynamicTabs, {
        props: {
          modelValue: 'tab1',
          tabs: mockTabs,
          typeStyle
        }
      })

      expect((wrapper.vm as any).typeStyle).toBe(typeStyle)
    })
  })

  it('should support tab icons', () => {
    const tabsWithIcon: TabItem[] = [
      { id: 'tab1', name: 'Tab 1', title: 'Tab with Icon', icon: 'Star' }
    ]

    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: tabsWithIcon
      }
    })

    expect((wrapper.vm as any).tabs[0].icon).toBe('Star')
  })

  it('should support tab badges', () => {
    const tabsWithBadge: TabItem[] = [
      { id: 'tab1', name: 'Tab 1', title: 'Tab with Badge', badge: 5 },
      { id: 'tab2', name: 'Tab 2', title: 'Tab with Zero Badge', badge: 0 }
    ]

    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: tabsWithBadge
      }
    })

    expect((wrapper.vm as any).tabs[0].badge).toBe(5)
    expect((wrapper.vm as any).tabs[1].badge).toBe(0)
  })

  it('should support disabled tabs', () => {
    const tabsWithDisabled: TabItem[] = [
      { id: 'tab1', name: 'Tab 1', title: 'Normal Tab' },
      { id: 'tab2', name: 'Tab 2', title: 'Disabled Tab', disabled: true }
    ]

    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: tabsWithDisabled
      }
    })

    expect((wrapper.vm as any).tabs[1].disabled).toBe(true)
  })

  it('should support lazy loading tabs', () => {
    const tabsWithLazy: TabItem[] = [
      { id: 'tab1', name: 'Tab 1', title: 'Eager Tab', lazy: true },
      { id: 'tab2', name: 'Tab 2', title: 'Default Lazy Tab' }
    ]

    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: tabsWithLazy
      }
    })

    expect((wrapper.vm as any).tabs[0].lazy).toBe(true)
    // Default is lazy !== false, which means true
    expect((wrapper.vm as any).tabs[1].lazy).toBeUndefined()
  })

  it('should emit update:modelValue when activeTab changes', async () => {
    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: mockTabs
      }
    })

    const vm = wrapper.vm as any
    vm.activeTab = 'tab2'
    await nextTick()

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })

  it('should emit remove event when tab is removed', async () => {
    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: mockTabs
      }
    })

    const vm = wrapper.vm as any
    vm.handleRemove('tab3')
    await nextTick()

    const removeEmitted = wrapper.emitted('remove')
    expect(removeEmitted).toBeTruthy()
    // Remove event emits [targetName, tab]
    expect(removeEmitted![0][0]).toBe('tab3')
    expect(removeEmitted![0][1]).toEqual(expect.objectContaining({ id: 'tab3' }))
  })

  it('should emit add event when tab is added', () => {
    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: mockTabs,
        addable: true
      }
    })

    const vm = wrapper.vm as any
    vm.handleAdd()

    expect(wrapper.emitted('add')).toBeTruthy()
    expect(wrapper.emitted('edit')).toBeTruthy()
  })

  it('should emit change event when tab changes', () => {
    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: mockTabs
      }
    })

    const vm = wrapper.vm as any
    vm.handleChange('tab2')

    expect(wrapper.emitted('change')).toBeTruthy()
  })

  it('should handle tab content as string', () => {
    const tabsWithContent: TabItem[] = [
      { id: 'tab1', name: 'Tab 1', title: 'Tab with HTML', content: '<p>Content</p>' }
    ]

    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: tabsWithContent
      }
    })

    expect((wrapper.vm as any).tabs[0].content).toBe('<p>Content</p>')
  })

  it('should handle tab content as component', () => {
    const MockComponent = markRaw({ template: '<div>Mock Component</div>' })

    const tabsWithComponent: TabItem[] = [
      { id: 'tab1', name: 'Tab 1', title: 'Tab with Component', component: MockComponent, props: { test: 'value' } }
    ]

    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: tabsWithComponent
      }
    })

    expect((wrapper.vm as any).tabs[0].component).toBeDefined()
    expect((wrapper.vm as any).tabs[0].props).toEqual({ test: 'value' })
  })

  it('should handle tab with both id and name', () => {
    const tabsWithId: TabItem[] = [
      { id: 'unique-id-1', name: 'tab1', title: 'Tab with ID' }
    ]

    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'unique-id-1',
        tabs: tabsWithId
      }
    })

    expect((wrapper.vm as any).tabs[0].id).toBe('unique-id-1')
    expect((wrapper.vm as any).tabs[0].name).toBe('tab1')
  })

  it('should handle tab without id (fallback to name)', () => {
    const tabsWithoutId: TabItem[] = [
      { name: 'tab1', title: 'Tab without ID' }
    ]

    const wrapper = mount(DynamicTabs, {
      props: {
        modelValue: 'tab1',
        tabs: tabsWithoutId
      }
    })

    expect((wrapper.vm as any).tabs[0].id).toBeUndefined()
    expect((wrapper.vm as any).tabs[0].name).toBe('tab1')
  })
})
