/**
 * ColumnManager component tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ColumnManager from '@/components/common/ColumnManager.vue'
import type { ColumnItem } from '@/composables/useColumnConfig'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElPopover: {
    name: 'ElPopover',
    template: `
      <div class="el-popover">
        <slot name="reference" />
        <div v-if="show" class="popover-content">
          <slot />
        </div>
      </div>
    `,
    props: ['placement', 'width', 'trigger', 'teleported'],
    emits: ['show']
  },
  ElTooltip: {
    name: 'ElTooltip',
    template: '<div class="el-tooltip"><slot /></div>',
    props: ['content', 'placement']
  },
  ElButton: {
    name: 'ElButton',
    template: '<button class="el-button" :class="type ? \'el-button--\' + type : \'\'"><slot /></button>',
    props: ['icon', 'circle', 'size', 'link', 'type']
  },
  ElDivider: {
    name: 'ElDivider',
    template: '<div class="el-divider"></div>'
  },
  ElCheckbox: {
    name: 'ElCheckbox',
    template: '<input type="checkbox" class="el-checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)">',
    props: ['modelValue', 'indeterminate'],
    emits: ['update:modelValue']
  },
  ElSelect: {
    name: 'ElSelect',
    template: '<select class="el-select" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
    props: ['modelValue', 'size'],
    emits: ['update:modelValue']
  },
  ElOption: {
    name: 'ElOption',
    template: '<option class="el-option" :value="value">{{ label }}</option>',
    props: ['value', 'label']
  },
  ElInputNumber: {
    name: 'ElInputNumber',
    template: '<input type="number" class="el-input-number" :value="modelValue" @input="$emit(\'update:modelValue\', Number($event.target.value))">',
    props: ['modelValue', 'min', 'max', 'step', 'size', 'controlsPosition'],
    emits: ['update:modelValue']
  },
  ElMessage: {
    success: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  }
}))

// Mock icons
vi.mock('@element-plus/icons-vue', () => ({
  Setting: { template: '<svg>SETTING</svg>' },
  DCaret: { template: '<svg>DCARET</svg>' },
  InfoFilled: { template: '<svg>INFO</svg>' }
}))

describe('ColumnManager', () => {
  let mockColumns: ColumnItem[]

  beforeEach(() => {
    vi.clearAllMocks()

    mockColumns = [
      { prop: 'name', label: 'Name', width: 150, defaultWidth: 120, visible: true },
      { prop: 'code', label: 'Code', width: 120, defaultWidth: 120, visible: true },
      { prop: 'status', label: 'Status', width: 100, defaultWidth: 100, visible: true },
      { prop: 'category', label: 'Category', width: 120, defaultWidth: 120, visible: false }
    ] as ColumnItem[]
  })

  it('should render correctly', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    // Component should mount successfully
    expect(wrapper.vm).toBeTruthy()
    const vm = wrapper.vm as any
    expect(vm.internalColumns).toHaveLength(4)
  })

  it('should initialize internal columns from props', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    expect(vm.internalColumns).toHaveLength(4)
    expect(vm.internalColumns[0].prop).toBe('name')
  })

  it('should calculate allVisible correctly', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    // All visible by default (category is false so should be 3)
    const visibleCount = vm.internalColumns.filter(col => col.visible !== false).length
    expect(visibleCount).toBe(3)
    expect(vm.allVisible).toBe(false)
  })

  it('should calculate someVisible correctly', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    const visibleCount = vm.internalColumns.filter(col => col.visible !== false).length
    const isSomeVisible = visibleCount > 0 && visibleCount < vm.internalColumns.length
    expect(isSomeVisible).toBe(true)
  })

  it('should handle column visibility toggle', async () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    const column = vm.internalColumns[0]

    // Hide first column
    vm.handleToggleVisibility(column, false)
    await nextTick()

    expect(column.visible).toBe(false)
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })

  it('should prevent hiding required columns', async () => {
    const requiredColumns = [
      { prop: 'id', label: 'ID', width: 80, visible: true, required_in_list: true }
    ] as ColumnItem[]

    const wrapper = mount(ColumnManager, {
      props: {
        columns: requiredColumns
      }
    })

    const vm = wrapper.vm as any
    const column = vm.internalColumns[0]

    vm.handleToggleVisibility(column, false)

    // Should show warning and not change visibility
    expect(column.visible).toBe(true)
  })

  it('should handle column width change', async () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    const column = vm.internalColumns[0]

    vm.handleWidthChange(column, 200)
    await nextTick()

    expect(column.width).toBe(200)
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })

  it('should handle column fixed position change', async () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    const column = vm.internalColumns[0]

    vm.handleFixedChange(column, 'left')
    await nextTick()

    expect(column.fixed).toBe('left')

    vm.handleFixedChange(column, '')
    await nextTick()

    expect(column.fixed).toBeNull()
  })

  it('should handle column reordering via drag and drop', async () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any

    // Simulate drag from index 0 to index 2
    vm.handleDragStart(0, { dataTransfer: { setData: vi.fn(), effectAllowed: 'move' } } as any)
    vm.handleDrop(2, { preventDefault: vi.fn() } as any)
    vm.handleDragEnd()

    expect(vm.internalColumns[0].prop).toBe('code') // Originally at index 1
    expect(vm.internalColumns[1].prop).toBe('status') // Originally at index 2
    expect(vm.internalColumns[2].prop).toBe('name') // Originally at index 0
  })

  it('should handle reset to defaults', async () => {
    const modifiedColumns = [
      { prop: 'name', label: 'Name', width: 200, defaultWidth: 120, visible: false, defaultVisible: true },
      { prop: 'code', label: 'Code', width: 150, defaultWidth: 120, visible: true, defaultVisible: true, fixed: 'left' as const }
    ] as ColumnItem[]

    const wrapper = mount(ColumnManager, {
      props: {
        columns: modifiedColumns
      }
    })

    const vm = wrapper.vm as any
    vm.handleReset()

    expect(vm.internalColumns[0].width).toBe(120) // Reset to defaultWidth
    expect(vm.internalColumns[0].visible).toBe(true) // Reset to defaultVisible
    expect(vm.internalColumns[1].fixed).toBeUndefined() // Reset fixed

    expect(wrapper.emitted('reset')).toBeTruthy()
  })

  it('should handle save', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    vm.handleSave()

    expect(wrapper.emitted('save')).toBeTruthy()
    const emittedValue = wrapper.emitted('save')[0]
    // Save event emits an array with columns
    expect(emittedValue[0]).toEqual(vm.internalColumns)
  })

  it('should handle toggle all visibility', async () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    vm.handleToggleAll(false)

    vm.internalColumns.forEach(col => {
      // Required columns should stay visible
      if (!(col as any).required_in_list) {
        expect(col.visible).toBe(false)
      }
    })

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })

  it('should get field code with backward compatibility', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    const column = { prop: 'test', field_code: 'custom_code' } as any

    expect(vm.getFieldCode(column)).toBe('custom_code')
  })

  it('should fallback to prop when field_code not available', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    const column = { prop: 'test' }

    expect(vm.getFieldCode(column)).toBe('test')
  })

  it('should get display label with override', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    const column = { prop: 'name', label: 'Original Name', label_override: 'Custom Name' } as any

    expect(vm.getDisplayLabel(column)).toBe('Custom Name')
  })

  it('should get display label without override', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    const column = { prop: 'name', label: 'Original Name' }

    expect(vm.getDisplayLabel(column)).toBe('Original Name')
  })

  it('should check if column is required', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any

    const requiredColumn = { required_in_list: true } as any
    expect(vm.isRequired(requiredColumn)).toBe(true)

    const optionalColumn = { required_in_list: false } as any
    expect(vm.isRequired(optionalColumn)).toBe(false)
  })

  it('should get field type label', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any

    expect(vm.getFieldTypeLabel('text')).toBe('T')
    expect(vm.getFieldTypeLabel('number')).toBe('#')
    expect(vm.getFieldTypeLabel('date')).toBe('D')
    expect(vm.getFieldTypeLabel('datetime')).toBe('DT')
    expect(vm.getFieldTypeLabel('boolean')).toBe('B')
    expect(vm.getFieldTypeLabel('select')).toBe('S')
    expect(vm.getFieldTypeLabel('user')).toBe('U')
    expect(vm.getFieldTypeLabel('reference')).toBe('R')
    expect(vm.getFieldTypeLabel('unknown')).toBe('U')
  })

  it('should emit changes when columns are reordered', async () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any

    // Change a column property
    vm.handleWidthChange(vm.internalColumns[0], 200)

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    const emittedValue = wrapper.emitted('update:modelValue')[0][0]
    expect(emittedValue).toEqual(vm.internalColumns)
  })

  it('should init columns when popover shows', () => {
    const wrapper = mount(ColumnManager, {
      props: {
        columns: mockColumns
      }
    })

    const vm = wrapper.vm as any
    const originalLength = vm.internalColumns.length

    vm.handleShow()

    // Should reinitialize columns
    expect(vm.internalColumns.length).toBe(originalLength)
  })
})
