import { describe, expect, it } from 'vitest'

import {
  createPortalAssetStatusOptions,
  formatPortalAssetValue,
  getPortalAssetDetailPath,
  getPortalAssetStatusTagType,
} from './portalAssetModel'

const t = (key: string) => key

describe('portalAssetModel', () => {
  it('maps asset detail paths and status tags to canonical values', () => {
    expect(getPortalAssetDetailPath('asset-1')).toBe('/objects/Asset/asset-1')
    expect(getPortalAssetStatusTagType('under_maintenance')).toBe('warning')
    expect(getPortalAssetStatusTagType('unknown')).toBe('info')
  })

  it('formats asset values and status filter options', () => {
    expect(formatPortalAssetValue(12345, t)).toBe('common.units.yuan 12,345')
    expect(formatPortalAssetValue(null, t)).toBe('-')
    expect(createPortalAssetStatusOptions(t)).toHaveLength(4)
  })
})
