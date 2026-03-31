import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import DesignerCanvasSectionRenderer from '@/components/designer/DesignerCanvasSectionRenderer.vue'

const stubs = {
  FieldDisplay: {
    name: 'FieldDisplay',
    props: ['field', 'value'],
    template: '<div data-testid="field-display-stub">{{ Array.isArray(value) ? value.length : 0 }}</div>'
  },
  'el-button': { template: '<button><slot /></button>' },
  'el-icon': { template: '<i><slot /></i>' },
  'designer-canvas-field-renderer': { template: '<div />' },
  'el-tabs': { template: '<div><slot /></div>' },
  'el-tab-pane': { template: '<div><slot /></div>' },
  'el-collapse': { template: '<div><slot /></div>' },
  'el-collapse-item': { template: '<div><slot /></div>' }
}

describe('DesignerCanvasSectionRenderer', () => {
  it('renders a live detail-region table preview from configured child columns', () => {
    const wrapper = mount(DesignerCanvasSectionRenderer, {
      props: {
        renderSection: {
          id: 'detail_region_1',
          title: 'Pickup Items',
          type: 'detail-region',
          position: 'main',
          collapsible: false,
          collapsed: false,
          fields: [],
          tabs: [],
          items: [],
          section: {
            id: 'detail_region_1',
            type: 'detail-region',
            title: 'Pickup Items',
            fieldCode: 'items',
            relationCode: 'pickup_items',
            targetObjectCode: 'PickupItem',
            relatedFields: [
              { code: 'quantity', label: 'Quantity', fieldType: 'number', minWidth: 160, fixed: 'right' },
              { code: 'remark', label: 'Remark', fieldType: 'text' }
            ]
          }
        },
        sectionIndex: 0,
        totalSectionCount: 1,
        isDesignMode: false,
        selectedId: '',
        activeTabName: '',
        activeCollapseNames: [],
        sizeFeedbackFieldId: '',
        sampleData: {},
        cardTitles: {
          remove: 'Remove',
          resize: 'Resize',
          reset: 'Reset',
          sidebarOnlyHeight: 'Sidebar only'
        },
        sectionActionLabels: {
          moveUp: 'Up',
          moveDown: 'Down',
          reorder: 'Reorder'
        },
        toCanvasField: (field: any) => field,
        fieldToDesignDisplayField: () => ({ prop: 'unused', label: 'Unused', type: 'text', visible: true }),
        getSampleValue: (field: any) => {
          if (field.fieldType === 'number') return 100
          return 'Sample Text'
        },
        selectSection: () => {},
        maybeSelectSection: () => {},
        maybeSelectField: () => {},
        removeField: () => {},
        updateFieldLabel: () => {},
        handleFieldSizeReset: () => {},
        handleFieldResizeStart: () => {},
        toggleSectionCollapse: () => {},
        moveSection: () => {},
        deleteSection: () => {},
        handleSectionDragStart: () => {},
        handleDragEnd: () => {},
        handleTabDrop: () => {},
        handleCollapseDrop: () => {},
        handleSectionDrop: () => {},
        handleSectionDragOver: () => {},
        handleSectionDragLeave: () => {},
        t: (key: string) => key
      },
      global: {
        stubs
      }
    })

    expect(wrapper.find('[data-testid="detail-region-live-preview"]').exists()).toBe(true)

    const fieldDisplay = wrapper.findComponent({ name: 'FieldDisplay' })
    expect(fieldDisplay.exists()).toBe(true)
    expect(fieldDisplay.props('field')).toMatchObject({
      fieldType: 'sub_table',
      componentProps: {
        columns: [
          expect.objectContaining({ key: 'quantity', minWidth: 160, fixed: 'right' }),
          expect.objectContaining({ key: 'remark' })
        ]
      }
    })
    expect(fieldDisplay.props('value')).toEqual([
      { quantity: 100, remark: 'Sample Text 1' },
      { quantity: 101, remark: 'Sample Text 2' },
      { quantity: 102, remark: 'Sample Text 3' }
    ])
  })
})
