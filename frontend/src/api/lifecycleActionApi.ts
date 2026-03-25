import request from '@/utils/request'

type MutationPayload = Record<string, unknown>

export const purchaseRequestActionApi = {
  submit(id: string): Promise<any> {
    return request.post(`/lifecycle/purchase-requests/${id}/submit/`)
  },
  approve(id: string, decision: 'approved' | 'rejected', comment?: string): Promise<any> {
    return request.post(`/lifecycle/purchase-requests/${id}/approve/`, { decision, comment })
  },
  cancel(id: string, reason?: string): Promise<any> {
    return request.post(`/lifecycle/purchase-requests/${id}/cancel/`, { reason })
  },
  complete(id: string): Promise<any> {
    return request.post(`/lifecycle/purchase-requests/${id}/complete/`)
  },
  items(id: string): Promise<any[]> {
    return request.get(`/lifecycle/purchase-requests/${id}/items/`)
  },
  pendingApproval(): Promise<any[]> {
    return request.get('/lifecycle/purchase-requests/pending_approval/')
  }
}

export const assetReceiptActionApi = {
  submitInspection(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-receipts/${id}/submit_inspection/`)
  },
  inspect(id: string, result: string, passed: boolean): Promise<any> {
    return request.post(`/lifecycle/asset-receipts/${id}/inspect/`, { result, passed })
  },
  generateAssets(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-receipts/${id}/generate_assets/`)
  },
  cancel(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-receipts/${id}/cancel/`)
  },
  items(id: string): Promise<any[]> {
    return request.get(`/lifecycle/asset-receipts/${id}/items/`)
  }
}

export const maintenanceActionApi = {
  assign(id: string, technicianId: string): Promise<any> {
    return request.post(`/lifecycle/maintenance/${id}/assign/`, { technician_id: technicianId })
  },
  startWork(id: string): Promise<any> {
    return request.post(`/lifecycle/maintenance/${id}/start_work/`)
  },
  completeWork(id: string, data: MutationPayload): Promise<any> {
    return request.post(`/lifecycle/maintenance/${id}/complete_work/`, data)
  },
  verify(id: string, result: string): Promise<any> {
    return request.post(`/lifecycle/maintenance/${id}/verify/`, { result })
  },
  cancel(id: string, reason?: string): Promise<any> {
    return request.post(`/lifecycle/maintenance/${id}/cancel/`, { reason })
  },
  statistics(): Promise<any> {
    return request.get('/lifecycle/maintenance/statistics/')
  },
  urgent(): Promise<any[]> {
    return request.get('/lifecycle/maintenance/urgent/')
  }
}

export const maintenancePlanActionApi = {
  activate(id: string): Promise<any> {
    return request.post(`/lifecycle/maintenance-plans/${id}/activate/`)
  },
  pause(id: string): Promise<any> {
    return request.post(`/lifecycle/maintenance-plans/${id}/pause/`)
  },
  archive(id: string): Promise<any> {
    return request.post(`/lifecycle/maintenance-plans/${id}/archive/`)
  },
  generateTasks(id: string): Promise<{ generated_count: number }> {
    return request.post(`/lifecycle/maintenance-plans/${id}/generate_tasks/`)
  }
}

export const disposalRequestActionApi = {
  submit(id: string): Promise<any> {
    return request.post(`/lifecycle/disposal-requests/${id}/submit/`)
  },
  startAppraisal(id: string): Promise<any> {
    return request.post(`/lifecycle/disposal-requests/${id}/start_appraisal/`)
  },
  approve(id: string, decision: 'approved' | 'rejected', comment?: string): Promise<any> {
    return request.post(`/lifecycle/disposal-requests/${id}/approve/`, { decision, comment })
  },
  cancel(id: string, reason?: string): Promise<any> {
    return request.post(`/lifecycle/disposal-requests/${id}/cancel/`, { reason })
  },
  items(id: string): Promise<any[]> {
    return request.get(`/lifecycle/disposal-requests/${id}/items/`)
  }
}

export const maintenanceTaskActionApi = {
  execute(id: string, data: { execution_result: string; actual_hours: number }): Promise<any> {
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

export const assetWarrantyActionApi = {
  activate(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-warranties/${id}/activate/`)
  },
  expire(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-warranties/${id}/expire/`)
  },
  renew(id: string, data: { end_date: string; warranty_cost?: number }): Promise<any> {
    return request.post(`/lifecycle/asset-warranties/${id}/renew/`, data)
  },
  recordClaim(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-warranties/${id}/record_claim/`)
  },
  cancel(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-warranties/${id}/cancel/`)
  },
  expiringSoon(): Promise<any[]> {
    return request.get('/lifecycle/asset-warranties/expiring_soon/')
  },
  statistics(): Promise<any> {
    return request.get('/lifecycle/asset-warranties/statistics/')
  }
}
