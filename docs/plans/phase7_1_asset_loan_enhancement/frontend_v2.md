# Phase 7.1: Asset Loan Enhancement - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement enhanced asset loan functionality with loan extensions, return handling, and loan history tracking.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/loan.ts

export interface AssetLoan {
  id: string
  loanNo: string
  borrowerId: string
  borrower?: User
  loanDate: string
  expectedReturnDate: string
  actualReturnDate?: string
  loanReason: string
  status: LoanStatus
  items: LoanItem[]
  approvals: ApprovalRecord[]
  organizationId: string
  createdAt: string
  createdBy: string
}

export interface LoanItem {
  id: string
  assetId: string
  asset?: Asset
  quantity: number
  remark?: string
}

export enum LoanStatus {
  DRAFT = 'draft',
  PENDING = 'pending',
  APPROVED = 'approved',
  IN_USE = 'in_use',
  OVERDUE = 'overdue',
  RETURNED = 'returned',
  CANCELLED = 'cancelled'
}

export interface LoanExtension {
  loanId: string
  newExpectedReturnDate: string
  reason: string
}

export interface AssetReturn {
  loanId: string
  returnDate: string
  items: ReturnItem[]
  remark?: string
}

export interface ReturnItem {
  loanItemId: string
  condition: 'good' | 'damaged' | 'lost'
  remark?: string
}
```

### API Service

```typescript
// frontend/src/api/loans.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  AssetLoan,
  LoanExtension,
  AssetReturn,
  LoanStatus,
  LoanCreate,
  LoanUpdate
} from '@/types/loan'

export const loanApi = {
  list(filters?: any): Promise<PaginatedResponse<AssetLoan>> {
    return request.get('/assets/loans/', { params: filters })
  },

  get(id: string): Promise<AssetLoan> {
    return request.get(`/assets/loans/${id}/`)
  },

  create(data: LoanCreate): Promise<AssetLoan> {
    return request.post('/assets/loans/', data)
  },

  update(id: string, data: LoanUpdate): Promise<AssetLoan> {
    return request.put(`/assets/loans/${id}/`, data)
  },

  submit(id: string): Promise<void> {
    return request.post(`/assets/loans/${id}/submit/`)
  },

  approve(id: string, data: { action: 'approve' | 'reject'; comment?: string }): Promise<void> {
    return request.post(`/assets/loans/${id}/approve/`, data)
  },

  requestExtension(id: string, data: LoanExtension): Promise<void> {
    return request.post(`/assets/loans/${id}/extend/`, data)
  },

  returnAsset(id: string, data: AssetReturn): Promise<void> {
    return request.post(`/assets/loans/${id}/return/`, data)
  },

  cancel(id: string, reason?: string): Promise<void> {
    return request.post(`/assets/loans/${id}/cancel/`, { reason })
  },

  getOverdueLoans(): Promise<AssetLoan[]> {
    return request.get('/assets/loans/overdue/')
  }
}
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/loan.ts` | Loan type definitions |
| `frontend/src/api/loans.ts` | Loan API service |
| `frontend/src/views/loans/LoanList.vue` | Loan list page |
| `frontend/src/views/loans/LoanForm.vue` | Loan form page |
| `frontend/src/views/loans/ReturnDialog.vue` | Return dialog component |
