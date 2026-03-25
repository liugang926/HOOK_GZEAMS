import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import SectionPropertyEditor from '../SectionPropertyEditor.vue'

vi.mock('vue-i18n', () => ({
  createI18n: () => ({
    global: {
      t: (key: string) => key,
      te: () => false
    }
  }),
  useI18n: () => ({
    t: (key: string) => key,
    locale: { value: 'en-US' }
  })
}))

const stubs = {
  'el-form': { name: 'el-form', template: '<form><slot /></form>' },
  'el-divider': { name: 'el-divider', template: '<hr />' },
  'el-form-item': {
    name: 'el-form-item',
    props: ['label'],
    template: '<div class="form-item-stub" :data-label="label"><slot /></div>'
  },
  'el-switch': { name: 'el-switch', template: '<div class="el-switch-stub"></div>' },
  'el-select': { name: 'el-select', template: '<div class="el-select-stub"><slot /></div>' },
  'el-option': {
    name: 'el-option',
    props: ['label', 'value'],
    template: '<div class="el-option-stub" :data-label="label" :data-value="value"></div>'
  },
  'el-radio-group': { name: 'el-radio-group', template: '<div class="el-radio-group-stub"><slot /></div>' },
  'el-radio-button': { name: 'el-radio-button', template: '<button class="el-radio-button-stub"><slot /></button>' },
  'el-input': { name: 'el-input', template: '<div class="el-input-stub"></div>' },
  'el-button': { name: 'el-button', template: '<button class="el-button-stub"><slot /></button>' }
}

const createDragTransfer = () => ({
  effectAllowed: '',
  dropEffect: '',
  setData: vi.fn()
})

describe('SectionPropertyEditor', () => {
  it('renders core section properties from schema', () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: { type: 'section', title: 'Basic', columns: 2 },
        sectionType: 'section'
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toEqual(expect.arrayContaining(['Title', 'Columns', 'Border', 'Collapsible']))
  })

  it('hides section-only properties for tab section type', () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: { type: 'tab', title: 'Tab Group' },
        sectionType: 'tab'
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toContain('Title')
    expect(labels).not.toContain('Border')
  })

  it('emits update events when section property changes', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: { type: 'section', title: 'Old Title' },
        sectionType: 'section'
      },
      global: { stubs }
    })

    const input = wrapper.findComponent({ name: 'el-input' })
    expect(input.exists()).toBe(true)

    input.vm.$emit('input', 'New Title')
    await nextTick()

    const emitted = wrapper.emitted('update-property')
    expect(emitted).toBeTruthy()
    expect(emitted?.[0]?.[0]).toEqual({ key: 'title', value: 'New Title' })
  })

  it('preserves earlier changes when multiple section properties update quickly', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'section',
          title: 'Basic',
          columns: 2,
          collapsible: false,
          collapsed: false
        },
        sectionType: 'section'
      },
      global: { stubs }
    })

    const columnsItem = wrapper.findAll('.form-item-stub').find((node) => node.attributes('data-label') === 'Columns')
    const collapsibleItem = wrapper.findAll('.form-item-stub').find((node) => node.attributes('data-label') === 'Collapsible')

    expect(columnsItem).toBeTruthy()
    expect(collapsibleItem).toBeTruthy()

    columnsItem!.findComponent({ name: 'el-radio-group' }).vm.$emit('change', 1)
    await nextTick()
    collapsibleItem!.findComponent({ name: 'el-switch' }).vm.$emit('change', true)
    await nextTick()

    const emittedModelValues = wrapper.emitted('update:modelValue') || []
    expect(emittedModelValues.at(-1)?.[0]).toMatchObject({
      columns: 1,
      collapsible: true
    })
  })

  it('uses aggregate detail-region options and hides derived metadata fields', () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'detail-region',
          relationCode: 'pickup_items'
        },
        sectionType: 'detail-region',
        detailRegionOptions: [
          {
            relationCode: 'pickup_items',
            fieldCode: 'items',
            title: '领用明细',
            titleEn: 'Pickup Items',
            targetObjectCode: 'PickupItem',
            targetObjectName: '领用明细',
            targetObjectNameEn: 'Pickup Item',
            targetObjectLocaleNames: {
              'zh-CN': '领用明细',
              'en-US': 'Pickup Item'
            }
          }
        ]
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toContain('Relation Code')
    expect(labels).not.toContain('Field Code')
    expect(labels).not.toContain('Target Object Code')
    expect(labels).toContain('Related Fields')
    expect(labels).toContain('Lookup Columns')

    expect(wrapper.findAll('.el-option-stub').length).toBeGreaterThan(0)

    const meta = wrapper.find('[data-testid="detail-region-meta"]')
    expect(meta.exists()).toBe(true)
    expect(meta.text()).toContain('items')
    expect(meta.text()).toContain('领用明细')
  })

  it('parses json updates for detail-region child field config', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'detail-region',
          relatedFields: [{ code: 'asset', label: 'Asset' }]
        },
        sectionType: 'detail-region'
      },
      global: { stubs }
    })

    const jsonInput = wrapper.find('[data-testid="section-prop-relatedFields"]').findComponent({ name: 'el-input' })
    expect(jsonInput.exists()).toBe(true)

    jsonInput.vm.$emit('input', '[{\"code\":\"quantity\",\"label\":\"Quantity\",\"fieldType\":\"number\"}]')
    await nextTick()

    const emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [{ code: 'quantity', label: 'Quantity', fieldType: 'number' }]
    })
  })

  it('builds child field config from visual detail-region selection', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'detail-region',
          relationCode: 'pickup_items'
        },
        sectionType: 'detail-region',
        detailRegionFieldOptions: {
          pickup_items: [
            { code: 'asset', label: 'Asset', fieldType: 'reference', referenceObject: 'Asset' },
            { code: 'quantity', label: 'Quantity', fieldType: 'number' }
          ]
        }
      },
      global: { stubs }
    })

    const select = wrapper.find('[data-testid="section-prop-relatedFields"]').findComponent({ name: 'el-select' })
    expect(select.exists()).toBe(true)

    select.vm.$emit('change', ['asset', 'quantity'])
    await nextTick()

    const emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          referenceObject: 'Asset'
        },
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number'
        }
      ]
    })
  })

  it('shows preset recommendations and preview details for numeric child fields', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'detail-region',
          relationCode: 'pickup_items',
          relatedFields: [
            { code: 'quantity', label: 'Quantity', fieldType: 'number' }
          ]
        },
        sectionType: 'detail-region',
        detailRegionFieldOptions: {
          pickup_items: [
            { code: 'quantity', label: 'Quantity', fieldType: 'number' }
          ]
        }
      },
      global: { stubs }
    })

    const presetField = wrapper.find('[data-testid="detail-region-relatedFields-preset-quantity"]')
    const presetOptions = presetField.findAll('.el-option-stub').map((node) => node.attributes('data-label'))
    expect(presetOptions).toEqual(['Default', 'Amount', 'Amount Summary'])

    const recommendation = wrapper.find('[data-testid="detail-region-relatedFields-preset-recommendation-quantity"]')
    expect(recommendation.exists()).toBe(true)
    expect(recommendation.text()).toContain('Recommended: Amount / Amount Summary')

    presetField.findComponent({ name: 'el-select' }).vm.$emit('change', 'amountSummary')
    await nextTick()

    const description = wrapper.find('[data-testid="detail-region-relatedFields-preset-description-quantity"]')
    expect(description.exists()).toBe(true)
    expect(description.text()).toContain('Right-aligned summary amount column for totals or rollups.')

    const preview = wrapper.find('[data-testid="detail-region-relatedFields-preset-preview-quantity"]')
    expect(preview.exists()).toBe(true)
    expect(preview.text()).toContain('Preview')
    expect(preview.text()).toContain('Min 160px')
    expect(preview.text()).toContain('Right aligned')
    expect(preview.text()).toContain('Fixed right')
    expect(preview.text()).toContain('Number')
    expect(preview.text()).toContain('Empty: 0')
  })

  it('temporarily previews preset interactions before applying them', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'detail-region',
          relationCode: 'pickup_items',
          relatedFields: [
            { code: 'quantity', label: 'Quantity', fieldType: 'number' }
          ]
        },
        sectionType: 'detail-region',
        detailRegionFieldOptions: {
          pickup_items: [
            { code: 'quantity', label: 'Quantity', fieldType: 'number' }
          ]
        }
      },
      global: { stubs }
    })

    const actions = wrapper.find('[data-testid="detail-region-relatedFields-preset-actions-quantity"]')
    expect(actions.exists()).toBe(true)
    expect(actions.text()).toContain('Try presets')

    const trigger = wrapper.find('[data-testid="detail-region-relatedFields-preset-trigger-quantity-amountSummary"]')
    expect(trigger.exists()).toBe(true)

    await trigger.trigger('mouseenter')
    await nextTick()

    expect((wrapper.emitted('update-property') || []).length).toBe(0)
    const previewEmitted = wrapper.emitted('preview-property') || []
    expect(previewEmitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          label: 'Quantity',
          fieldType: 'number',
          fieldCode: 'quantity',
          name: 'Quantity',
          field_type: 'number',
          minWidth: 160,
          align: 'right',
          fixed: 'right',
          formatter: 'number',
          emptyText: '0'
        }
      ]
    })

    const hint = wrapper.find('[data-testid="detail-region-relatedFields-preset-hint-quantity"]')
    expect(hint.exists()).toBe(true)
    expect(hint.text()).toContain('Previewing Amount Summary. Click a preset to apply.')

    const preview = wrapper.find('[data-testid="detail-region-relatedFields-preset-preview-quantity"]')
    expect(preview.exists()).toBe(true)
    expect(preview.text()).toContain('Fixed right')

    await actions.trigger('mouseleave')
    await nextTick()

    expect(wrapper.find('[data-testid="detail-region-relatedFields-preset-hint-quantity"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="detail-region-relatedFields-preset-recommendation-quantity"]').exists()).toBe(true)
    expect((wrapper.emitted('update-property') || []).length).toBe(0)
    expect((wrapper.emitted('preview-property') || []).at(-1)?.[0]).toBeNull()

    const applyTrigger = wrapper.find('[data-testid="detail-region-relatedFields-preset-trigger-quantity-amountSummary"]')
    expect(applyTrigger.exists()).toBe(true)

    await applyTrigger.trigger('click')
    await nextTick()

    const emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          minWidth: 160,
          align: 'right',
          fixed: 'right',
          formatter: 'number',
          emptyText: '0'
        }
      ]
    })
  })

  it('previews and applies section-level detail-region templates as a single patch', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'detail-region',
          relationCode: 'pickup_items',
          fieldCode: 'items'
        },
        sectionType: 'detail-region',
        detailRegionOptions: [
          {
            relationCode: 'pickup_items',
            fieldCode: 'items',
            title: 'Pickup Items',
            titleEn: 'Pickup Items',
            targetObjectCode: 'PickupItem',
            targetObjectName: 'Pickup Item',
            targetObjectNameEn: 'Pickup Item',
            targetObjectLocaleNames: {
              'zh-CN': '领用明细',
              'en-US': 'Pickup Item'
            },
            detailEditMode: 'inline_table',
            toolbarConfig: {
              addRow: true,
              import: true
            },
            relatedFields: [
              { code: 'asset', label: 'Asset', fieldType: 'reference' },
              { code: 'quantity', label: 'Quantity', fieldType: 'number' },
              { code: 'remark', label: 'Remark', fieldType: 'text' },
              { code: 'status', label: 'Status', fieldType: 'select' }
            ],
            lookupColumns: [
              { code: 'asset', label: 'Asset', fieldType: 'reference' },
              { code: 'status', label: 'Status', fieldType: 'select' },
              { code: 'updatedAt', label: 'Updated At', fieldType: 'datetime' }
            ]
          }
        ]
      },
      global: { stubs }
    })

    const trigger = wrapper.find('[data-testid="detail-region-section-preset-trigger-sidebarSummary"]')
    expect(trigger.exists()).toBe(true)

    await trigger.trigger('mouseenter')
    await nextTick()

    expect((wrapper.emitted('preview-property') || []).at(-1)?.[0]).toEqual({
      values: expect.objectContaining({
        position: 'sidebar',
        detailEditMode: 'readonly_table',
        relatedFields: [
          expect.objectContaining({ code: 'asset' }),
          expect.objectContaining({ code: 'status' }),
          expect.objectContaining({ code: 'updatedAt' })
        ]
      })
    })

    const hint = wrapper.find('[data-testid="detail-region-section-preset-hint"]')
    expect(hint.exists()).toBe(true)
    expect(hint.text()).toContain('Sidebar Summary')

    await trigger.trigger('click')
    await nextTick()

    const emittedBatch = wrapper.emitted('update-properties') || []
    expect(emittedBatch.at(-1)?.[0]).toMatchObject({
      position: 'sidebar',
      detailEditMode: 'readonly_table',
      toolbarConfig: {}
    })
    expect(wrapper.find('[data-testid="detail-region-section-preset-preview"]').text()).toContain('3 columns')
  })

  it('supports drag sorting for selected related fields', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'detail-region',
          relationCode: 'pickup_items',
          relatedFields: [
            { code: 'asset', label: 'Asset', fieldType: 'reference' },
            { code: 'quantity', label: 'Quantity', fieldType: 'number' }
          ]
        },
        sectionType: 'detail-region',
        detailRegionFieldOptions: {
          pickup_items: [
            { code: 'asset', label: 'Asset', fieldType: 'reference', referenceObject: 'Asset' },
            { code: 'quantity', label: 'Quantity', fieldType: 'number' }
          ]
        }
      },
      global: { stubs }
    })

    const assetItem = wrapper.find('[data-testid="detail-region-relatedFields-item-asset"]')
    const quantityItem = wrapper.find('[data-testid="detail-region-relatedFields-item-quantity"]')
    expect(assetItem.exists()).toBe(true)
    expect(quantityItem.exists()).toBe(true)

    Object.defineProperty(assetItem.element, 'getBoundingClientRect', {
      configurable: true,
      value: () => ({
        top: 0,
        bottom: 40,
        left: 0,
        right: 240,
        width: 240,
        height: 40,
        x: 0,
        y: 0,
        toJSON: () => ({})
      })
    })

    await quantityItem.trigger('dragstart', { dataTransfer: createDragTransfer() })
    await assetItem.trigger('dragover', { clientY: 4, dataTransfer: createDragTransfer() })
    await assetItem.trigger('drop', { clientY: 4, dataTransfer: createDragTransfer() })
    await nextTick()

    const emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number'
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          referenceObject: 'Asset'
        }
      ]
    })
  })

  it('supports reordering, width updates, and removal for selected related fields', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'detail-region',
          relationCode: 'pickup_items',
          relatedFields: [
            { code: 'asset', label: 'Asset', fieldType: 'reference', width: 220 },
            { code: 'quantity', label: 'Quantity', fieldType: 'number' }
          ]
        },
        sectionType: 'detail-region',
        detailRegionFieldOptions: {
          pickup_items: [
            { code: 'asset', label: 'Asset', fieldType: 'reference', referenceObject: 'Asset' },
            { code: 'quantity', label: 'Quantity', fieldType: 'number' }
          ]
        }
      },
      global: { stubs }
    })

    const moveUp = wrapper
      .find('[data-testid="detail-region-relatedFields-move-up-quantity"]')
      .findComponent({ name: 'el-button' })
    moveUp.vm.$emit('click')
    await nextTick()

    let emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number'
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          width: 220,
          referenceObject: 'Asset'
        }
      ]
    })

    const widthInput = wrapper
      .find('[data-testid="detail-region-relatedFields-width-quantity"]')
      .findComponent({ name: 'el-input' })
    widthInput.vm.$emit('input', '320')
    await nextTick()

    emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          width: 320
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          width: 220,
          referenceObject: 'Asset'
        }
      ]
    })

    const minWidthInput = wrapper
      .find('[data-testid="detail-region-relatedFields-min-width-quantity"]')
      .findComponent({ name: 'el-input' })
    minWidthInput.vm.$emit('input', '180')
    await nextTick()

    emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          width: 320,
          minWidth: 180
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          width: 220,
          referenceObject: 'Asset'
        }
      ]
    })

    const alignSelect = wrapper
      .find('[data-testid="detail-region-relatedFields-align-quantity"]')
      .findComponent({ name: 'el-select' })
    alignSelect.vm.$emit('change', 'right')
    await nextTick()

    emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          width: 320,
          minWidth: 180,
          align: 'right'
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          width: 220,
          referenceObject: 'Asset'
        }
      ]
    })

    const fixedSelect = wrapper
      .find('[data-testid="detail-region-relatedFields-fixed-quantity"]')
      .findComponent({ name: 'el-select' })
    fixedSelect.vm.$emit('change', 'right')
    await nextTick()

    emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          width: 320,
          minWidth: 180,
          align: 'right',
          fixed: 'right'
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          width: 220,
          referenceObject: 'Asset'
        }
      ]
    })

    const ellipsisSwitch = wrapper
      .find('[data-testid="detail-region-relatedFields-ellipsis-quantity"]')
      .findComponent({ name: 'el-switch' })
    ellipsisSwitch.vm.$emit('change', true)
    await nextTick()

    emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          width: 320,
          minWidth: 180,
          align: 'right',
          fixed: 'right',
          ellipsis: true,
          showOverflowTooltip: true,
          show_overflow_tooltip: true
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          width: 220,
          referenceObject: 'Asset'
        }
      ]
    })

    const formatterSelect = wrapper
      .find('[data-testid="detail-region-relatedFields-formatter-quantity"]')
      .findComponent({ name: 'el-select' })
    formatterSelect.vm.$emit('change', 'number')
    await nextTick()

    emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          width: 320,
          minWidth: 180,
          align: 'right',
          fixed: 'right',
          ellipsis: true,
          showOverflowTooltip: true,
          show_overflow_tooltip: true,
          formatter: 'number'
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          width: 220,
          referenceObject: 'Asset'
        }
      ]
    })

    const emptyTextInput = wrapper
      .find('[data-testid="detail-region-relatedFields-empty-text-quantity"]')
      .findComponent({ name: 'el-input' })
    emptyTextInput.vm.$emit('input', '0')
    await nextTick()

    emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          width: 320,
          minWidth: 180,
          align: 'right',
          fixed: 'right',
          ellipsis: true,
          showOverflowTooltip: true,
          show_overflow_tooltip: true,
          formatter: 'number',
          emptyText: '0'
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          width: 220,
          referenceObject: 'Asset'
        }
      ]
    })

    const tooltipTemplateInput = wrapper
      .find('[data-testid="detail-region-relatedFields-tooltip-template-quantity"]')
      .findComponent({ name: 'el-input' })
    tooltipTemplateInput.vm.$emit('input', 'Qty: {value}')
    await nextTick()

    emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          width: 320,
          minWidth: 180,
          align: 'right',
          fixed: 'right',
          ellipsis: true,
          showOverflowTooltip: true,
          show_overflow_tooltip: true,
          formatter: 'number',
          emptyText: '0',
          tooltipTemplate: 'Qty: {value}'
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          width: 220,
          referenceObject: 'Asset'
        }
      ]
    })

    const presetSelect = wrapper
      .find('[data-testid="detail-region-relatedFields-preset-quantity"]')
      .findComponent({ name: 'el-select' })
    presetSelect.vm.$emit('change', 'status')
    await nextTick()

    emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          width: 320,
          minWidth: 120,
          align: 'center',
          ellipsis: true,
          showOverflowTooltip: true,
          show_overflow_tooltip: true,
          tooltipTemplate: '{value}'
        },
        {
          code: 'asset',
          fieldCode: 'asset',
          label: 'Asset',
          name: 'Asset',
          fieldType: 'reference',
          field_type: 'reference',
          width: 220,
          referenceObject: 'Asset'
        }
      ]
    })

    const remove = wrapper
      .find('[data-testid="detail-region-relatedFields-remove-asset"]')
      .findComponent({ name: 'el-button' })
    remove.vm.$emit('click')
    await nextTick()

    emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [
        {
          code: 'quantity',
          fieldCode: 'quantity',
          label: 'Quantity',
          name: 'Quantity',
          fieldType: 'number',
          field_type: 'number',
          width: 320,
          minWidth: 120,
          align: 'center',
          ellipsis: true,
          showOverflowTooltip: true,
          show_overflow_tooltip: true,
          tooltipTemplate: '{value}'
        }
      ]
    })
  })

  it('supports width updates for selected lookup columns', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'detail-region',
          relationCode: 'pickup_items',
          lookupColumns: [
            { key: 'asset', label: 'Asset', width: 240, align: 'left' },
            { key: 'quantity', label: 'Quantity' }
          ]
        },
        sectionType: 'detail-region',
        detailRegionFieldOptions: {
          pickup_items: [
            { code: 'asset', label: 'Asset', fieldType: 'reference' },
            { code: 'quantity', label: 'Quantity', fieldType: 'number', width: 180 }
          ]
        }
      },
      global: { stubs }
    })

    const widthInput = wrapper
      .find('[data-testid="detail-region-lookupColumns-width-quantity"]')
      .findComponent({ name: 'el-input' })
    widthInput.vm.$emit('input', '280')
    await nextTick()

    const emitted = wrapper.emitted('update-property') || []
    expect(emitted.at(-1)?.[0]).toEqual({
      key: 'lookupColumns',
      value: [
        { key: 'asset', label: 'Asset', width: 240, minWidth: undefined, align: 'left' },
        { key: 'quantity', label: 'Quantity', width: 280, minWidth: undefined }
      ]
    })

    const minWidthInput = wrapper
      .find('[data-testid="detail-region-lookupColumns-min-width-quantity"]')
      .findComponent({ name: 'el-input' })
    minWidthInput.vm.$emit('input', '160')
    await nextTick()

    const alignSelect = wrapper
      .find('[data-testid="detail-region-lookupColumns-align-quantity"]')
      .findComponent({ name: 'el-select' })
    alignSelect.vm.$emit('change', 'center')
    await nextTick()

    const fixedSelect = wrapper
      .find('[data-testid="detail-region-lookupColumns-fixed-quantity"]')
      .findComponent({ name: 'el-select' })
    fixedSelect.vm.$emit('change', 'right')
    await nextTick()

    const ellipsisSwitch = wrapper
      .find('[data-testid="detail-region-lookupColumns-ellipsis-quantity"]')
      .findComponent({ name: 'el-switch' })
    ellipsisSwitch.vm.$emit('change', true)
    await nextTick()

    const formatterSelect = wrapper
      .find('[data-testid="detail-region-lookupColumns-formatter-quantity"]')
      .findComponent({ name: 'el-select' })
    formatterSelect.vm.$emit('change', 'number')
    await nextTick()

    const emptyTextInput = wrapper
      .find('[data-testid="detail-region-lookupColumns-empty-text-quantity"]')
      .findComponent({ name: 'el-input' })
    emptyTextInput.vm.$emit('input', '0')
    await nextTick()

    const tooltipTemplateInput = wrapper
      .find('[data-testid="detail-region-lookupColumns-tooltip-template-quantity"]')
      .findComponent({ name: 'el-input' })
    tooltipTemplateInput.vm.$emit('input', 'Qty: {value}')
    await nextTick()

    const updated = wrapper.emitted('update-property') || []
    expect(updated.at(-1)?.[0]).toEqual({
      key: 'lookupColumns',
      value: [
        { key: 'asset', label: 'Asset', width: 240, minWidth: undefined, align: 'left' },
        {
          key: 'quantity',
          label: 'Quantity',
          width: 280,
          minWidth: 160,
          align: 'center',
          fixed: 'right',
          ellipsis: true,
          showOverflowTooltip: true,
          show_overflow_tooltip: true,
          formatter: 'number',
          emptyText: '0',
          tooltipTemplate: 'Qty: {value}'
        }
      ]
    })

    const presetSelect = wrapper
      .find('[data-testid="detail-region-lookupColumns-preset-quantity"]')
      .findComponent({ name: 'el-select' })
    presetSelect.vm.$emit('change', 'amountSummary')
    await nextTick()

    const presetUpdated = wrapper.emitted('update-property') || []
    expect(presetUpdated.at(-1)?.[0]).toEqual({
      key: 'lookupColumns',
      value: [
        { key: 'asset', label: 'Asset', width: 240, minWidth: undefined, align: 'left' },
        {
          key: 'quantity',
          label: 'Quantity',
          width: 280,
          minWidth: 160,
          align: 'right',
          fixed: 'right',
          formatter: 'number',
          emptyText: '0'
        }
      ]
    })
  })
})
