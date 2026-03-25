import { reactive, ref } from 'vue'

import { assetApi } from '@/api/assets'
import { purchaseRequestApi, maintenanceApi, disposalRequestApi } from '@/api/dynamic'
import { maintenanceTaskActionApi } from '@/api/lifecycleActionApi'
import { workflowNodeApi } from '@/api/workflow'

import {
  buildDisposalActivities,
  buildMaintenanceActivities,
  buildPurchaseRequestActivities,
  createDashboardLifecycleState,
  createDashboardMetricsState,
  normalizeOverdueTaskCount,
  sortDashboardActivities,
  type DashboardActivityItem
} from './dashboardModel'

type TranslationFn = (key: string) => string

export const useDashboardData = (t: TranslationFn) => {
  const metrics = reactive(createDashboardMetricsState())
  const lifecycleLoading = ref(true)
  const lifecycle = reactive(createDashboardLifecycleState())
  const recentActivities = ref<DashboardActivityItem[]>([])

  const fetchMetrics = async () => {
    let byStatus: Record<string, number> = {}
    let byCategory: Record<string, number> = {}

    try {
      const stats = await assetApi.statistics()
      if (stats) {
        metrics.assetCount = stats.total || 0
        metrics.assetValue = (stats.total_value || 0).toLocaleString()
        byStatus = stats.by_status || {}
        byCategory = stats.by_category || {}
      }

      const tasks = await workflowNodeApi.getMyTasks({ page: 1, pageSize: 1, status: 'pending' })
      metrics.pendingApproval = tasks?.count || 0
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    }

    return {
      byCategory,
      byStatus,
    }
  }

  const fetchLifecycleData = async () => {
    lifecycleLoading.value = true
    const activities: DashboardActivityItem[] = []

    await Promise.allSettled([
      (async () => {
        const response = await purchaseRequestApi.list({ status: 'submitted', pageSize: 5 }) as any
        lifecycle.pendingPurchases = response?.count ?? 0
        activities.push(...buildPurchaseRequestActivities((response?.results ?? []).slice(0, 3), t))
      })(),
      (async () => {
        const [reportedResponse, processingResponse] = await Promise.all([
          maintenanceApi.list({ status: 'reported', pageSize: 1 }) as any,
          maintenanceApi.list({ status: 'processing', pageSize: 3 }) as any
        ])

        lifecycle.activeMaintenance = (reportedResponse?.count ?? 0) + (processingResponse?.count ?? 0)
        activities.push(...buildMaintenanceActivities((processingResponse?.results ?? []).slice(0, 2), t))
      })(),
      (async () => {
        const response = await maintenanceTaskActionApi.overdue() as any
        lifecycle.overdueTasks = normalizeOverdueTaskCount(response)
      })(),
      (async () => {
        const response = await disposalRequestApi.list({ status: 'submitted', pageSize: 5 }) as any
        lifecycle.pendingDisposals = response?.count ?? 0
        activities.push(...buildDisposalActivities((response?.results ?? []).slice(0, 2), t))
      })()
    ])

    recentActivities.value = sortDashboardActivities(activities)
    lifecycleLoading.value = false
  }

  return {
    fetchLifecycleData,
    fetchMetrics,
    lifecycle,
    lifecycleLoading,
    metrics,
    recentActivities,
  }
}
