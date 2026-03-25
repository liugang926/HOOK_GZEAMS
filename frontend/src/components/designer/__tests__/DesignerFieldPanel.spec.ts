import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import DesignerFieldPanel from '../DesignerFieldPanel.vue'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (_key: string, fallback?: string) => fallback || _key
  })
}))

const globalStubs = {
  'el-input': { template: '<div class="el-input-stub"></div>' },
  'el-progress': {
    props: ['percentage'],
    template: '<div class="el-progress-stub">{{ percentage }}</div>'
  },
  'el-icon': { template: '<i><slot /></i>' },
  ArrowRight: true,
  Search: true,
  Grid: true,
  Document: true,
  Ticket: true,
  FolderOpened: true
}

const buildDetailRegionOptions = () => ([
  {
    templateCode: 'pickup_items:sidebarSummary',
    presetCode: 'sidebarSummary',
    relationCode: 'pickup_items',
    fieldCode: 'items',
    title: 'Pickup Items · Sidebar Summary',
    groupTitle: 'Pickup Items',
    groupMeta: 'Pickup Item',
    variantTitle: 'Sidebar Summary',
    targetObjectCode: 'PickupItem',
    targetObjectLabel: 'Pickup Item',
    description: 'Compact sidebar summary with a focused subset of child columns.'
  },
  {
    templateCode: 'pickup_items:editableDetail',
    presetCode: 'editableDetail',
    relationCode: 'pickup_items',
    fieldCode: 'items',
    title: 'Pickup Items · Editable Detail',
    groupTitle: 'Pickup Items',
    groupMeta: 'Pickup Item',
    variantTitle: 'Editable Detail',
    targetObjectCode: 'PickupItem',
    targetObjectLabel: 'Pickup Item',
    description: 'Main-area editable child table with metadata-backed detail columns and toolbar actions.',
    preset: {
      detailEditMode: 'inline_table',
      collapsible: true
    }
  },
  {
    templateCode: 'pickup_items:reviewTable',
    presetCode: 'reviewTable',
    relationCode: 'pickup_items',
    fieldCode: 'items',
    title: 'Pickup Items · Review Table',
    groupTitle: 'Pickup Items',
    groupMeta: 'Pickup Item',
    variantTitle: 'Review Table',
    targetObjectCode: 'PickupItem',
    targetObjectLabel: 'Pickup Item',
    description: 'Readonly review table that prefers lookup columns for quick checking.',
    preset: {
      detailEditMode: 'readonly_table',
      collapsible: true
    }
  }
])

describe('DesignerFieldPanel', () => {
  it('renders assignment progress summary', () => {
    const wrapper = mount(DesignerFieldPanel, {
      props: {
        renderMode: 'design',
        searchQuery: '',
        assignedFieldCount: 2,
        totalFieldCount: 5,
        filteredFieldGroups: [],
        isGroupExpanded: () => true,
        canAddField: () => true,
        getDisabledReason: () => null,
        isFieldAdded: () => false
      },
      global: {
        stubs: globalStubs
      }
    })

    expect(wrapper.text()).toContain('2/5')
    expect(wrapper.find('.el-progress-stub').text()).toContain('40')
  })

  it('renders grouped detail-region palette cards and emits click events from a secondary variant', async () => {
    const wrapper = mount(DesignerFieldPanel, {
      props: {
        renderMode: 'design',
        searchQuery: '',
        assignedFieldCount: 2,
        totalFieldCount: 5,
        filteredFieldGroups: [],
        detailRegionOptions: buildDetailRegionOptions(),
        isGroupExpanded: () => true,
        canAddField: () => true,
        getDisabledReason: () => null,
        isFieldAdded: () => false,
        isDetailRegionAdded: () => false
      },
      global: {
        stubs: globalStubs
      }
    })

    expect(wrapper.findAll('[data-testid="layout-palette-detail-region-group-pickup_items"]')).toHaveLength(1)
    expect(wrapper.find('[data-testid="layout-palette-detail-region-pickup_items:editableDetail"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-item-pickup_items:reviewTable"]').exists()).toBe(false)

    await wrapper.find('[data-testid="layout-palette-detail-region-secondary-toggle-pickup_items"]').trigger('click')
    await wrapper.find('[data-testid="layout-palette-detail-region-secondary-item-pickup_items:reviewTable"]').trigger('click')

    expect(wrapper.emitted('detailRegionClick')?.[0]?.[0]).toMatchObject({
      templateCode: 'pickup_items:reviewTable',
      presetCode: 'reviewTable',
      relationCode: 'pickup_items',
      fieldCode: 'items',
      preset: {
        detailEditMode: 'readonly_table',
        collapsible: true
      }
    })
    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-menu-pickup_items"]').exists()).toBe(false)
  })

  it('collapses and expands detail-region groups from the subgroup header', async () => {
    const wrapper = mount(DesignerFieldPanel, {
      props: {
        renderMode: 'design',
        searchQuery: '',
        assignedFieldCount: 0,
        totalFieldCount: 5,
        filteredFieldGroups: [],
        detailRegionOptions: buildDetailRegionOptions(),
        isGroupExpanded: () => true,
        canAddField: () => true,
        getDisabledReason: () => null,
        isFieldAdded: () => false,
        isDetailRegionAdded: () => false
      },
      global: {
        stubs: globalStubs
      }
    })

    expect(wrapper.find('[data-testid="layout-palette-detail-region-group-grid-pickup_items"]').exists()).toBe(true)

    await wrapper.find('[data-testid="layout-palette-detail-region-group-toggle-pickup_items"]').trigger('click')

    expect(wrapper.find('[data-testid="layout-palette-detail-region-group-grid-pickup_items"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Editable Detail / Review Table / Sidebar Summary')

    await wrapper.find('[data-testid="layout-palette-detail-region-group-toggle-pickup_items"]').trigger('click')

    expect(wrapper.find('[data-testid="layout-palette-detail-region-group-grid-pickup_items"]').exists()).toBe(true)
  })

  it('keeps the primary detail-region visible and reveals secondary variants in a compact menu', async () => {
    const wrapper = mount(DesignerFieldPanel, {
      props: {
        renderMode: 'design',
        searchQuery: '',
        assignedFieldCount: 0,
        totalFieldCount: 5,
        filteredFieldGroups: [],
        detailRegionOptions: buildDetailRegionOptions(),
        isGroupExpanded: () => true,
        canAddField: () => true,
        getDisabledReason: () => null,
        isFieldAdded: () => false,
        isDetailRegionAdded: () => false
      },
      global: {
        stubs: globalStubs
      }
    })

    expect(wrapper.find('[data-testid="layout-palette-detail-region-pickup_items:editableDetail"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-menu-pickup_items"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="layout-palette-detail-region-pickup_items:reviewTable"]').exists()).toBe(false)

    await wrapper.find('[data-testid="layout-palette-detail-region-secondary-toggle-pickup_items"]').trigger('click')

    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-menu-pickup_items"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-item-pickup_items:reviewTable"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-item-pickup_items:sidebarSummary"]').exists()).toBe(true)

    await wrapper.find('[data-testid="layout-palette-detail-region-secondary-toggle-pickup_items"]').trigger('click')

    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-menu-pickup_items"]').exists()).toBe(false)
  })

  it('supports keyboard navigation for secondary detail-region variants', async () => {
    const wrapper = mount(DesignerFieldPanel, {
      attachTo: document.body,
      props: {
        renderMode: 'design',
        searchQuery: '',
        assignedFieldCount: 0,
        totalFieldCount: 5,
        filteredFieldGroups: [],
        detailRegionOptions: buildDetailRegionOptions(),
        isGroupExpanded: () => true,
        canAddField: () => true,
        getDisabledReason: () => null,
        isFieldAdded: () => false,
        isDetailRegionAdded: () => false
      },
      global: {
        stubs: globalStubs
      }
    })

    const toggle = wrapper.find('[data-testid="layout-palette-detail-region-secondary-toggle-pickup_items"]')

    await toggle.trigger('keydown', { key: 'ArrowDown' })
    await nextTick()

    const firstItem = wrapper.find('[data-testid="layout-palette-detail-region-secondary-item-pickup_items:reviewTable"]')
    const secondItem = wrapper.find('[data-testid="layout-palette-detail-region-secondary-item-pickup_items:sidebarSummary"]')

    expect(document.activeElement).toBe(firstItem.element)

    await firstItem.trigger('keydown', { key: 'ArrowDown' })
    await nextTick()

    expect(document.activeElement).toBe(secondItem.element)

    await secondItem.trigger('keydown', { key: 'Escape' })
    await nextTick()

    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-menu-pickup_items"]').exists()).toBe(false)
    expect(document.activeElement).toBe(toggle.element)

    wrapper.unmount()
  })

  it('applies a secondary detail-region variant with Enter', async () => {
    const wrapper = mount(DesignerFieldPanel, {
      attachTo: document.body,
      props: {
        renderMode: 'design',
        searchQuery: '',
        assignedFieldCount: 0,
        totalFieldCount: 5,
        filteredFieldGroups: [],
        detailRegionOptions: buildDetailRegionOptions(),
        isGroupExpanded: () => true,
        canAddField: () => true,
        getDisabledReason: () => null,
        isFieldAdded: () => false,
        isDetailRegionAdded: () => false
      },
      global: {
        stubs: globalStubs
      }
    })

    await wrapper.find('[data-testid="layout-palette-detail-region-secondary-toggle-pickup_items"]').trigger('keydown', { key: 'ArrowDown' })
    await nextTick()

    const firstItem = wrapper.find('[data-testid="layout-palette-detail-region-secondary-item-pickup_items:reviewTable"]')
    await firstItem.trigger('keydown', { key: 'Enter' })

    expect(wrapper.emitted('detailRegionClick')?.[0]?.[0]).toMatchObject({
      templateCode: 'pickup_items:reviewTable',
      presetCode: 'reviewTable'
    })
    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-menu-pickup_items"]').exists()).toBe(false)

    wrapper.unmount()
  })

  it('emits preview events for secondary detail-region variants on hover and focus', async () => {
    const wrapper = mount(DesignerFieldPanel, {
      props: {
        renderMode: 'design',
        searchQuery: '',
        assignedFieldCount: 0,
        totalFieldCount: 5,
        filteredFieldGroups: [],
        detailRegionOptions: buildDetailRegionOptions(),
        isGroupExpanded: () => true,
        canAddField: () => true,
        getDisabledReason: () => null,
        isFieldAdded: () => false,
        isDetailRegionAdded: () => false
      },
      global: {
        stubs: globalStubs
      }
    })

    await wrapper.find('[data-testid="layout-palette-detail-region-secondary-toggle-pickup_items"]').trigger('click')

    const reviewItem = wrapper.find('[data-testid="layout-palette-detail-region-secondary-item-pickup_items:reviewTable"]')
    await reviewItem.trigger('mouseenter')
    await reviewItem.trigger('focus')
    await wrapper.find('[data-testid="layout-palette-detail-region-secondary-menu-pickup_items"]').trigger('mouseleave')

    expect(wrapper.emitted('detailRegionPreview')?.[0]?.[0]).toMatchObject({
      templateCode: 'pickup_items:reviewTable',
      presetCode: 'reviewTable'
    })
    expect(wrapper.emitted('detailRegionPreview')?.[1]?.[0]).toMatchObject({
      templateCode: 'pickup_items:reviewTable',
      presetCode: 'reviewTable'
    })
    expect(wrapper.emitted('detailRegionPreview')?.[2]?.[0]).toBeNull()
  })

  it('shows secondary variants inline while searching to keep results discoverable', () => {
    const wrapper = mount(DesignerFieldPanel, {
      props: {
        renderMode: 'design',
        searchQuery: 'review',
        assignedFieldCount: 0,
        totalFieldCount: 5,
        filteredFieldGroups: [],
        detailRegionOptions: buildDetailRegionOptions(),
        isGroupExpanded: () => true,
        canAddField: () => true,
        getDisabledReason: () => null,
        isFieldAdded: () => false,
        isDetailRegionAdded: () => false
      },
      global: {
        stubs: globalStubs
      }
    })

    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-grid-pickup_items"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="layout-palette-detail-region-pickup_items:reviewTable"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="layout-palette-detail-region-secondary-toggle-pickup_items"]').exists()).toBe(false)
  })

  it('renders section template palette cards and emits click events', async () => {
    const wrapper = mount(DesignerFieldPanel, {
      props: {
        renderMode: 'design',
        searchQuery: '',
        assignedFieldCount: 0,
        totalFieldCount: 5,
        filteredFieldGroups: [],
        sectionTemplateOptions: [
          {
            templateCode: 'tab-main',
            templateType: 'tab',
            title: 'Tab Pages',
            description: 'Tabbed section for switching grouped content',
            icon: 'tab',
            preset: {
              position: 'main',
              columns: 2
            }
          }
        ],
        isGroupExpanded: () => true,
        canAddField: () => true,
        getDisabledReason: () => null,
        isFieldAdded: () => false
      },
      global: {
        stubs: globalStubs
      }
    })

    expect(wrapper.text()).toContain('Tab Pages')
    expect(wrapper.text()).toContain('Tabbed section for switching grouped content')

    await wrapper.find('[data-testid="layout-palette-section-template-tab-main"]').trigger('click')

    expect(wrapper.emitted('sectionTemplateClick')?.[0]?.[0]).toMatchObject({
      templateCode: 'tab-main',
      templateType: 'tab',
      preset: {
        position: 'main',
        columns: 2
      }
    })
  })
})
