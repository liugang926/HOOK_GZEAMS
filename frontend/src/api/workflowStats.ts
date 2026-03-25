/**
 * Workflow Statistics API Service
 *
 * API methods for fetching workflow monitoring dashboard data.
 */

import request from '@/utils/request'

export interface OverviewStats {
  total_instances: number
  pending_instances: number
  completed_instances: number
  rejected_instances: number
  my_pending_tasks: number
  my_completed_tasks: number
  my_overdue_tasks: number
  average_completion_hours: number
  approval_rate: number
  overdue_rate: number
  instances_by_status: Record<string, number>
  instances_by_definition: Record<string, number>
}

export interface TrendDataPoint {
  date: string
  started: number
  completed: number
  rejected: number
}

export interface TrendsResponse {
  period: string
  data: TrendDataPoint[]
}

export interface BottleneckNode {
  node_name: string
  definition_name: string
  avg_duration_hours: number
  task_count: number
  overdue_count: number
  overdue_rate: number
}

export interface PerformanceDefinition {
  definition_name: string
  definition_code: string
  total_instances: number
  approved: number
  rejected: number
  running: number
  approval_rate: number
  avg_completion_hours: number
}

export const workflowStatsApi = {
  /**
   * Get overview statistics.
   */
  getOverview(): Promise<any> {
    return request.get('/workflows/statistics/')
  },

  /**
   * Get daily instance trends.
   */
  getTrends(period: '7d' | '14d' | '30d' = '7d'): Promise<any> {
    return request.get('/workflows/statistics/trends/', { params: { period } })
  },

  /**
   * Get slowest approval nodes.
   */
  getBottlenecks(): Promise<any> {
    return request.get('/workflows/statistics/bottlenecks/')
  },

  /**
   * Get per-definition performance metrics.
   */
  getPerformance(): Promise<any> {
    return request.get('/workflows/statistics/performance/')
  },
}
