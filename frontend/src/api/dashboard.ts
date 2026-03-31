/**
 * Dashboard API service.
 *
 * Provides access to the aggregated dashboard summary endpoint.
 */
import request from '@/utils/request'

export interface AssetSummary {
  totalAssets: number
  inUse: number
  idle: number
  maintenance: number
  disposed: number
}

export interface MyTasks {
  pendingApprovals: number
  pendingPickups: number
  overdueTasks: number
}

export interface DashboardAlert {
  type: 'warning' | 'info' | 'error'
  title: string
  link: string
}

export interface QuickAction {
  code: string
  label: string
  icon: string
  route: string
}

export interface RecentActivity {
  action: string
  actor: string
  target: string
  timestamp: string
}

export interface DashboardSummary {
  assetSummary: AssetSummary
  myTasks: MyTasks
  alerts: DashboardAlert[]
  quickActions: QuickAction[]
  recentActivities: RecentActivity[]
}

export const dashboardApi = {
  /**
   * Fetch aggregated dashboard summary data.
   */
  getSummary: () => request.get<{ success: boolean; data: DashboardSummary }>('/dashboard/summary/'),
}
