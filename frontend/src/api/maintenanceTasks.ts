import request from '@/utils/request'
import { toData, toPaginated } from '@/api/contract'
import type { PaginatedResponse } from '@/types/api'
import { maintenanceTaskApi as dynamicMaintenanceTaskApi } from '@/api/dynamic'

type MaintenanceTaskExecutionPayload = {
  execution_result: string
  actual_hours: number
}

export const maintenanceTaskApi = {
  async list(params?: Record<string, unknown>): Promise<PaginatedResponse<any>> {
    return toPaginated<any>(await dynamicMaintenanceTaskApi.list(params))
  },
  async detail(id: string): Promise<any> {
    return toData<any>(await dynamicMaintenanceTaskApi.get(id))
  },
  execute(id: string, data: MaintenanceTaskExecutionPayload): Promise<any> {
    return request.post(`/lifecycle/maintenance-tasks/${id}/execute/`, data)
  },
  verify(id: string, verifyResult: string): Promise<any> {
    return request.post(`/lifecycle/maintenance-tasks/${id}/verify/`, { verify_result: verifyResult })
  },
  skip(id: string, reason: string): Promise<any> {
    return request.post(`/lifecycle/maintenance-tasks/${id}/skip/`, { reason })
  },
  overdue(): Promise<any[]> {
    return request.get('/lifecycle/maintenance-tasks/overdue/')
  },
  today(): Promise<any[]> {
    return request.get('/lifecycle/maintenance-tasks/today/')
  }
}

export default maintenanceTaskApi
