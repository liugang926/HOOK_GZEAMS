import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FieldDisplay from '../FieldDisplay.vue'

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    createI18n: () => ({
      global: {
        t: (key: string) => {
          if (key === 'common.yes') return 'Yes'
          if (key === 'common.no') return 'No'
          if (key === 'common.table.total') return 'Total'
          return key
        }
      }
    }),
    useI18n: () => ({
      t: (key: string) => {
        if (key === 'common.yes') return 'Yes'
        if (key === 'common.no') return 'No'
        if (key === 'common.table.total') return 'Total'
        return key
      }
    })
  }
})

describe('FieldDisplay', () => {
  it('formats sub-table cells using formatter, empty text, and tooltip template', () => {
    const wrapper = mount(FieldDisplay, {
      props: {
        field: {
          fieldType: 'sub_table',
          componentProps: {
            columns: [
              {
                key: 'quantity',
                label: 'Quantity',
                formatter: 'number',
                emptyText: '0',
                tooltipTemplate: 'Qty: {value}'
              },
              {
                key: 'status',
                label: 'Status',
                formatter: 'uppercase',
                tooltipTemplate: 'Status is {value}'
              }
            ]
          }
        },
        value: [
          { quantity: 1234, status: 'draft' },
          { quantity: '', status: '' }
        ]
      },
      global: {
        stubs: {
          'el-table': { template: '<div><slot /></div>' },
          'el-table-column': { template: '<div><slot :row="{}" /></div>' },
          'el-tooltip': { template: '<div><slot /></div>' },
          'el-image': true,
          'el-link': true,
          'el-tag': true,
          'el-rate': true,
          'el-icon': true,
          ReferenceRecordPill: true
        }
      }
    })

    const vm = wrapper.vm as any
    const [quantityColumn, statusColumn] = vm.subTableColumns

    expect(quantityColumn).toMatchObject({
      key: 'quantity',
      formatter: 'number',
      emptyText: '0',
      tooltipTemplate: 'Qty: {value}'
    })
    expect(vm.formatSubTableCell({ quantity: 1234 }, quantityColumn)).toBe('1,234')
    expect(vm.formatSubTableCell({ quantity: '' }, quantityColumn)).toBe('0')
    expect(vm.resolveSubTableTooltip({ quantity: 1234 }, quantityColumn)).toBe('Qty: 1,234')

    expect(vm.formatSubTableCell({ status: 'draft' }, statusColumn)).toBe('DRAFT')
    expect(vm.resolveSubTableTooltip({ status: 'draft' }, statusColumn)).toBe('Status is DRAFT')
  })
})
