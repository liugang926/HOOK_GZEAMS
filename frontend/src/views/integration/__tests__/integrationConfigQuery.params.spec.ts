import { describe, expect, it } from 'vitest'
import { buildIntegrationConfigQueryParams } from '@/views/integration/composables/integrationConfigQuery.params'

describe('buildIntegrationConfigQueryParams', () => {
  it('builds list and stats params with pagination only', () => {
    const result = buildIntegrationConfigQueryParams(
      {
        systemType: undefined,
        isEnabled: undefined,
        healthStatus: undefined
      },
      {
        page: 2,
        pageSize: 50
      }
    )

    expect(result).toEqual({
      listParams: {
        page: 2,
        page_size: 50
      },
      statsParams: {}
    })
  })

  it('keeps all active filters including boolean false', () => {
    const result = buildIntegrationConfigQueryParams(
      {
        systemType: 'sap',
        isEnabled: false,
        healthStatus: 'unhealthy'
      },
      {
        page: 1,
        pageSize: 20
      }
    )

    expect(result).toEqual({
      listParams: {
        page: 1,
        page_size: 20,
        systemType: 'sap',
        isEnabled: false,
        healthStatus: 'unhealthy'
      },
      statsParams: {
        systemType: 'sap',
        isEnabled: false,
        healthStatus: 'unhealthy'
      }
    })
  })
})
