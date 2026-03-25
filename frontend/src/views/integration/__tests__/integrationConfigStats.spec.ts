import { describe, expect, it } from 'vitest'
import {
  buildIntegrationStatsFromRows,
  createEmptyIntegrationStats
} from '@/views/integration/composables/integrationConfigStats'
import type { IntegrationConfig } from '@/types/integration'

const rows: IntegrationConfig[] = [
  {
    id: 'cfg-1',
    systemType: 'sap',
    systemName: 'SAP PROD',
    isEnabled: true,
    enabledModules: ['finance'],
    connectionConfig: {},
    syncConfig: {},
    healthStatus: 'healthy',
    lastSyncAt: null,
    lastSyncStatus: null
  },
  {
    id: 'cfg-2',
    systemType: 'odoo',
    systemName: 'Odoo',
    isEnabled: true,
    enabledModules: ['inventory'],
    connectionConfig: {},
    syncConfig: {},
    healthStatus: 'degraded',
    lastSyncAt: null,
    lastSyncStatus: null
  },
  {
    id: 'cfg-3',
    systemType: 'm18',
    systemName: 'M18',
    isEnabled: false,
    enabledModules: ['hr'],
    connectionConfig: {},
    syncConfig: {},
    healthStatus: 'unhealthy',
    lastSyncAt: null,
    lastSyncStatus: null
  }
]

describe('integrationConfigStats', () => {
  it('creates an empty stats object', () => {
    expect(createEmptyIntegrationStats()).toEqual({
      total: 0,
      healthy: 0,
      degraded: 0,
      unhealthy: 0
    })
  })

  it('builds aggregated health stats from rows', () => {
    expect(buildIntegrationStatsFromRows(rows, 25)).toEqual({
      total: 25,
      healthy: 1,
      degraded: 1,
      unhealthy: 1
    })
  })
})
