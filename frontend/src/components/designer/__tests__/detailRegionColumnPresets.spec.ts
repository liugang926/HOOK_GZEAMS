import { describe, expect, it } from 'vitest'
import {
  applyDetailRegionColumnPreset,
  getDetailRegionColumnPresetDefinitions,
  resolveDetailRegionColumnPreset
} from '../detailRegionColumnPresets'

describe('detailRegionColumnPresets', () => {
  it('applies amount preset while preserving unrelated column settings', () => {
    const result = applyDetailRegionColumnPreset(
      {
        code: 'quantity',
        width: 320,
        align: 'center',
        formatter: 'date',
        tooltipTemplate: 'Old'
      },
      'amount'
    )

    expect(result).toEqual({
      code: 'quantity',
      width: 320,
      minWidth: 140,
      align: 'right',
      formatter: 'number',
      emptyText: '0'
    })
  })

  it('replaces previous preset-managed config when switching presets', () => {
    const result = applyDetailRegionColumnPreset(
      {
        key: 'status',
        width: 240,
        minWidth: 140,
        align: 'right',
        formatter: 'number',
        emptyText: '0'
      },
      'status'
    )

    expect(result).toEqual({
      key: 'status',
      width: 240,
      minWidth: 120,
      align: 'center',
      ellipsis: true,
      showOverflowTooltip: true,
      show_overflow_tooltip: true,
      tooltipTemplate: '{value}'
    })
  })

  it('resolves matching preset code from logical column config', () => {
    expect(
      resolveDetailRegionColumnPreset({
        width: 300,
        min_width: 140,
        align: 'right',
        formatter: 'number',
        emptyText: '0'
      })
    ).toBe('amount')

    expect(
      resolveDetailRegionColumnPreset({
        minWidth: 120,
        align: 'center',
        ellipsis: true,
        showOverflowTooltip: true,
        tooltipTemplate: '{value}'
      })
    ).toBe('status')
  })

  it('applies summary and audit variants for business tables', () => {
    expect(
      applyDetailRegionColumnPreset(
        {
          key: 'amount',
          width: 240
        },
        'amountSummary'
      )
    ).toEqual({
      key: 'amount',
      width: 240,
      minWidth: 160,
      align: 'right',
      fixed: 'right',
      formatter: 'number',
      emptyText: '0'
    })

    expect(
      applyDetailRegionColumnPreset(
        {
          key: 'updated_at',
          width: 220
        },
        'auditDatetime'
      )
    ).toEqual({
      key: 'updated_at',
      width: 220,
      minWidth: 180,
      fixed: 'right',
      formatter: 'datetime',
      tooltipTemplate: '{value}'
    })
  })

  it('filters preset recommendations by field type when possible', () => {
    expect(getDetailRegionColumnPresetDefinitions('number').map((item) => item.code)).toEqual([
      'amount',
      'amountSummary'
    ])

    expect(getDetailRegionColumnPresetDefinitions('datetime').map((item) => item.code)).toEqual([
      'datetime',
      'auditDatetime'
    ])

    expect(getDetailRegionColumnPresetDefinitions('select').map((item) => item.code)).toEqual([
      'status',
      'statusCompact'
    ])
  })

  it('returns default when column config does not match a preset exactly', () => {
    expect(
      resolveDetailRegionColumnPreset({
        minWidth: 140,
        formatter: 'date',
        tooltipTemplate: '{value}'
      })
    ).toBe('')

    expect(
      applyDetailRegionColumnPreset(
        {
          key: 'quantity',
          width: 200,
          minWidth: 140,
          formatter: 'date'
        },
        ''
      )
    ).toEqual({
      key: 'quantity',
      width: 200
    })
  })
})
