import { describe, expect, it } from 'vitest'
import {
  buildLookupColumnConfigs,
  buildRelatedFieldConfigs,
  extractDetailRegionFieldOptions,
  extractLookupColumnKeys,
  extractRelatedFieldCodes
} from '@/components/designer/detailRegionFieldOptions'

describe('detailRegionFieldOptions', () => {
  it('extracts business child fields from runtime metadata', () => {
    const options = extractDetailRegionFieldOptions({
      objectCode: 'PickupItem',
      mode: 'edit',
      fields: {
        editableFields: [
          { code: 'id', name: 'ID', fieldType: 'text', isSystem: true },
          {
            code: 'asset',
            label: { 'zh-cn': 'Zi Chan', 'en-us': 'Asset' },
            fieldType: 'reference',
            referenceObject: 'Asset',
            minWidth: 180,
            align: 'right',
            fixed: 'left',
            ellipsis: true,
            formatter: 'uppercase',
            emptyText: 'N/A',
            tooltipTemplate: 'Asset: {value}'
          },
          { code: 'quantity', name: 'Quantity', fieldType: 'number' },
          { code: 'pickup', name: 'Pickup', is_reverse_relation: true, fieldType: 'reference' }
        ]
      }
    })

    expect(options).toEqual([
      expect.objectContaining({
        code: 'asset',
        label: expect.stringMatching(/Asset|Zi Chan/),
        fieldType: 'reference',
        referenceObject: 'Asset',
        targetObjectCode: 'Asset',
        minWidth: 180,
        align: 'right',
        fixed: 'left',
        ellipsis: true,
        formatter: 'uppercase',
        emptyText: 'N/A',
        tooltipTemplate: 'Asset: {value}',
        readonly: false,
        required: false
      }),
      expect.objectContaining({
        code: 'quantity',
        label: 'Quantity',
        fieldType: 'number',
        readonly: false,
        required: false
      })
    ])
  })

  it('builds related field configs and preserves existing overrides', () => {
    const configs = buildRelatedFieldConfigs(
      ['asset', 'quantity'],
      [
        {
          code: 'asset',
          label: 'Asset',
          fieldType: 'reference',
          referenceObject: 'Asset',
          minWidth: 180,
          align: 'left',
          fixed: 'left',
          ellipsis: true,
          formatter: 'uppercase',
          emptyText: 'N/A',
          tooltipTemplate: 'Asset: {value}'
        },
        {
          code: 'quantity',
          label: 'Quantity',
          fieldType: 'number',
          align: 'right',
          fixed: 'right',
          formatter: 'number',
          emptyText: '0',
          tooltipTemplate: 'Qty: {value}'
        }
      ],
      [{ code: 'asset', width: 240, componentProps: { readonly: true } }]
    )

    expect(configs).toEqual([
      {
        code: 'asset',
        fieldCode: 'asset',
        width: 240,
        minWidth: 180,
        align: 'left',
        fixed: 'left',
        ellipsis: true,
        showOverflowTooltip: true,
        show_overflow_tooltip: true,
        formatter: 'uppercase',
        emptyText: 'N/A',
        tooltipTemplate: 'Asset: {value}',
        label: 'Asset',
        name: 'Asset',
        fieldType: 'reference',
        field_type: 'reference',
        referenceObject: 'Asset',
        componentProps: { readonly: true },
        component_props: { readonly: true }
      },
      {
        code: 'quantity',
        fieldCode: 'quantity',
        label: 'Quantity',
        name: 'Quantity',
        fieldType: 'number',
        field_type: 'number',
        align: 'right',
        fixed: 'right',
        formatter: 'number',
        emptyText: '0',
        tooltipTemplate: 'Qty: {value}'
      }
    ])
  })

  it('builds lookup column configs and normalizes keys', () => {
    const configs = buildLookupColumnConfigs(
      ['asset', 'quantity'],
      [
        {
          code: 'asset',
          label: 'Asset',
          minWidth: 220,
          align: 'left',
          fixed: 'left',
          ellipsis: true,
          formatter: 'uppercase',
          emptyText: 'N/A',
          tooltipTemplate: 'Asset: {value}'
        },
        {
          code: 'quantity',
          label: 'Quantity',
          width: 160,
          align: 'center',
          fixed: 'right',
          formatter: 'number',
          emptyText: '0',
          tooltipTemplate: 'Qty: {value}'
        }
      ],
      [{ key: 'asset', width: 260 }]
    )

    expect(configs).toEqual([
      {
        key: 'asset',
        label: 'Asset',
        width: 260,
        minWidth: 220,
        align: 'left',
        fixed: 'left',
        ellipsis: true,
        showOverflowTooltip: true,
        show_overflow_tooltip: true,
        formatter: 'uppercase',
        emptyText: 'N/A',
        tooltipTemplate: 'Asset: {value}'
      },
      {
        key: 'quantity',
        label: 'Quantity',
        width: 160,
        minWidth: undefined,
        align: 'center',
        fixed: 'right',
        formatter: 'number',
        emptyText: '0',
        tooltipTemplate: 'Qty: {value}'
      }
    ])
    expect(extractRelatedFieldCodes([{ code: 'asset' }, { fieldCode: 'quantity' }])).toEqual(['asset', 'quantity'])
    expect(extractLookupColumnKeys([{ key: 'asset' }, 'quantity'])).toEqual(['asset', 'quantity'])
  })
})
