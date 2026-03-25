import type { IntegrationConfig, IntegrationStats } from '@/types/integration'

export const createEmptyIntegrationStats = (): IntegrationStats => ({
  total: 0,
  healthy: 0,
  degraded: 0,
  unhealthy: 0
})

export const buildIntegrationStatsFromRows = (
  rows: IntegrationConfig[],
  total: number
): IntegrationStats => ({
  total,
  healthy: rows.filter((row) => row.healthStatus === 'healthy').length,
  degraded: rows.filter((row) => row.healthStatus === 'degraded').length,
  unhealthy: rows.filter((row) => row.healthStatus === 'unhealthy').length
})
